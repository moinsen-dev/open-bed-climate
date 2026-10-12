//! OPL firmware update session. Port of `obc/fwupdate.py` (see there and docs/design/04-firmware-protocol.md).
//!
//! Pure logic, no flash access: `chunk()` returns a write plan (sectors to erase, where to program), the firmware
//! executes it and reports back with `written()`. Chunks arrive strictly in order; every FW frame is answered with
//! FW_STATUS (stop-and-wait), so the UART is idle while the flash is busy.

pub const SECTOR: u32 = 4096;
/// Data bytes per FW_CHUNK (one flash page; one UF2 block payload).
pub const CHUNK_MAX: usize = 256;
pub const FW_BEGIN_LEN: usize = 12;
pub const FW_STATUS_LEN: usize = 11;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FwState {
    Idle = 0,
    Receiving = 1,
    /// Image complete and verified; the MCU reboots into it.
    Done = 2,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FwResult {
    Ok = 0,
    /// A zone is on: switch every zone off first.
    Busy = 1,
    NoSession = 2,
    TooLarge = 3,
    BadOffset = 4,
    BadCrc = 5,
    FlashError = 6,
    BadPayload = 7,
    /// No A/B partition table in flash.
    NoPartitions = 8,
    Incomplete = 9,
}

/// CRC-32/ISO-HDLC (zlib), chainable: `crc32(b"6789", crc32(b"12345", 0)) == crc32(b"123456789", 0)`.
pub fn crc32(data: &[u8], crc: u32) -> u32 {
    let mut c = !crc;
    for &b in data {
        c ^= b as u32;
        for _ in 0..8 {
            c = if c & 1 != 0 { (c >> 1) ^ 0xEDB8_8320 } else { c >> 1 };
        }
    }
    !c
}

/// Image version word, as in the IMAGE_DEF VERSION item: 0xMMmmPPPP.
pub const fn version_word(major: u8, minor: u8, patch: u16) -> u32 {
    (major as u32) << 24 | (minor as u32) << 16 | patch as u32
}

/// The inactive A/B partition: physical flash offset (not an XIP address) and size.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct FwSlot {
    pub offset: u32,
    pub size: u32,
}

/// Erase `[erase_from, erase_to)` (whole sectors, possibly empty), then program the chunk's data at `addr`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct FwWrite {
    pub erase_from: u32,
    pub erase_to: u32,
    pub addr: u32,
}

#[derive(Clone, Debug)]
pub struct FwUpdate {
    state: FwState,
    slot: FwSlot,
    size: u32,
    crc_expected: u32,
    next_offset: u32,
    erased_to: u32,
    crc: u32,
}

impl Default for FwUpdate {
    fn default() -> Self {
        Self::new()
    }
}

fn u32_at(p: &[u8], i: usize) -> u32 {
    u32::from_le_bytes([p[i], p[i + 1], p[i + 2], p[i + 3]])
}

fn align_up(x: u32) -> u32 {
    x.div_ceil(SECTOR) * SECTOR
}

impl FwUpdate {
    pub const fn new() -> Self {
        Self {
            state: FwState::Idle,
            slot: FwSlot { offset: 0, size: 0 },
            size: 0,
            crc_expected: 0,
            next_offset: 0,
            erased_to: 0,
            crc: 0,
        }
    }

    pub fn state(&self) -> FwState {
        self.state
    }
    pub fn next_offset(&self) -> u32 {
        self.next_offset
    }
    /// A session is open (or finished and about to reboot): zones must stay off.
    pub fn active(&self) -> bool {
        self.state != FwState::Idle
    }
    pub fn slot(&self) -> FwSlot {
        self.slot
    }

    pub fn abort(&mut self) {
        *self = Self::new();
    }

    /// FW_BEGIN. `zones_idle`: every zone is off. `slot`: the inactive partition, `None` without a partition table.
    pub fn begin(&mut self, p: &[u8], slot: Option<FwSlot>, zones_idle: bool) -> FwResult {
        if p.len() != FW_BEGIN_LEN {
            return FwResult::BadPayload;
        }
        if !zones_idle {
            return FwResult::Busy;
        }
        let Some(slot) = slot else { return FwResult::NoPartitions };
        let size = u32_at(p, 0);
        self.abort();
        if size == 0 || size > slot.size {
            return FwResult::TooLarge;
        }
        self.state = FwState::Receiving;
        self.slot = slot;
        self.size = size;
        self.crc_expected = u32_at(p, 4);
        FwResult::Ok
    }

    /// FW_CHUNK: plan it. `(Ok, None)` = a resend of data already written: nothing to do, answer OK.
    pub fn chunk(&self, p: &[u8]) -> (FwResult, Option<FwWrite>) {
        if self.state != FwState::Receiving {
            return (FwResult::NoSession, None);
        }
        if p.len() < 5 || p.len() > 4 + CHUNK_MAX {
            return (FwResult::BadPayload, None);
        }
        let offset = u32_at(p, 0);
        let end = offset as u64 + (p.len() - 4) as u64;
        if end <= self.next_offset as u64 {
            return (FwResult::Ok, None);
        }
        if offset != self.next_offset || end > self.size as u64 {
            return (FwResult::BadOffset, None);
        }
        let erase_to = self.erased_to.max(align_up(end as u32));
        let base = self.slot.offset;
        (FwResult::Ok, Some(FwWrite { erase_from: base + self.erased_to, erase_to: base + erase_to, addr: base + offset }))
    }

    /// Report the outcome of the plan returned by `chunk(p)`.
    pub fn written(&mut self, p: &[u8], ok: bool) -> FwResult {
        if !ok {
            self.abort();
            return FwResult::FlashError;
        }
        let data = &p[4..];
        self.crc = crc32(data, self.crc);
        self.next_offset = u32_at(p, 0) + data.len() as u32;
        self.erased_to = self.erased_to.max(align_up(self.next_offset));
        FwResult::Ok
    }

    /// FW_END: on `Ok` the state is `Done` and the caller reboots into the new image.
    pub fn end(&mut self) -> FwResult {
        match self.state {
            FwState::Done => FwResult::Ok, // resent FW_END
            FwState::Idle => FwResult::NoSession,
            FwState::Receiving if self.next_offset != self.size => FwResult::Incomplete,
            FwState::Receiving if self.crc != self.crc_expected => {
                self.abort();
                FwResult::BadCrc
            }
            FwState::Receiving => {
                self.state = FwState::Done;
                FwResult::Ok
            }
        }
    }

    /// FW_STATUS payload: acked_seq:u8 state:u8 result:u8 next_offset:u32 running_version:u32.
    pub fn status(&self, acked_seq: u8, result: FwResult, running_version: u32) -> [u8; FW_STATUS_LEN] {
        let mut out = [0u8; FW_STATUS_LEN];
        out[0] = acked_seq;
        out[1] = self.state as u8;
        out[2] = result as u8;
        out[3..7].copy_from_slice(&self.next_offset.to_le_bytes());
        out[7..11].copy_from_slice(&running_version.to_le_bytes());
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn crc_reference() {
        assert_eq!(crc32(b"123456789", 0), 0xCBF4_3926);
        assert_eq!(crc32(b"6789", crc32(b"12345", 0)), 0xCBF4_3926);
    }

    #[test]
    fn offset_overflow_is_rejected() {
        let mut u = FwUpdate::new();
        let mut b = [0u8; 12];
        b[0..4].copy_from_slice(&100u32.to_le_bytes());
        assert_eq!(u.begin(&b, Some(FwSlot { offset: 0x20_0000, size: 0x10_0000 }), true), FwResult::Ok);
        let mut c = [0u8; 8];
        c[0..4].copy_from_slice(&u32::MAX.to_le_bytes());
        assert_eq!(u.chunk(&c).0, FwResult::BadOffset);
    }
}
