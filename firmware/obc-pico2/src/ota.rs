//! RP2350 bootrom glue for the OPL firmware update (obc-core::fwupdate holds the session logic).
//!
//! Uses the bootrom's A/B partitions and "try before you buy" (RP2350 datasheet, bootrom chapter):
//! - the flash carries a partition table with two linked app partitions A and B (`partitions.json`, installed once
//!   over USB, see firmware/README.md); the bootrom boots the one with the higher IMAGE_DEF version;
//! - the update is written into the partition the bootrom names for a UF2 of our family (the inactive one);
//! - a FLASH_UPDATE reboot boots it on trial. With the `tbyb` feature (release builds) the IMAGE_DEF is flagged
//!   "try before you buy": the new image must call `explicit_buy` (we do after `BUY_AFTER_S` of healthy control
//!   loop), which also erases the first sector of the other partition so the new one sticks regardless of versions;
//!   if it crashes or resets before that, the bootrom goes back to the previous partition. Without `tbyb` (dev builds)
//!   there is no rollback and the bootrom prefers the higher IMAGE_DEF version.
//!
//! UNTESTED ON HARDWARE. The ROM calls follow the datasheet and the pico-sdk headers (constants below).

use obc_core::fwupdate::FwSlot;

/// UF2 family id "rp2350-arm-s".
const FAMILY_RP2350_ARM_S: u32 = 0xe48b_ff59;
const SYS_INFO_BOOT_INFO: u32 = 0x0040;
const BOOT_TBYB_AND_UPDATE_FLAG_BUY_PENDING: u8 = 0x1;
const REBOOT2_FLAG_REBOOT_TYPE_FLASH_UPDATE: u32 = 0x4;
const REBOOT2_FLAG_NO_RETURN_ON_SUCCESS: u32 = 0x100;
const XIP_BASE: u32 = 0x1000_0000;
const LOCATION_SECTOR_BITS: u32 = 0x1fff;
const LOCATION_LAST_SECTOR_LSB: u32 = 13;

/// Seconds of healthy control loop before a trial image confirms itself (bootrom trial window is ~16.7 s).
pub const BUY_AFTER_S: u32 = 5;

#[repr(C, align(4))]
struct Workarea([u8; 4096]);

pub struct BootInfo {
    /// Partition we booted from; negative = none (no partition table).
    pub partition: i8,
    pub tbyb_flags: u8,
}

pub fn boot_info() -> Option<BootInfo> {
    let mut r = [0u32; 5];
    let n = unsafe { embassy_rp::rom_data::get_sys_info(r.as_mut_ptr(), r.len(), SYS_INFO_BOOT_INFO) };
    if n != r.len() as i32 || r[0] != SYS_INFO_BOOT_INFO {
        return None;
    }
    // word 1: diagnostic_partition_index:i8, boot_type:u8, partition:i8, tbyb_and_update_info:u8
    Some(BootInfo { partition: (r[1] >> 16) as u8 as i8, tbyb_flags: (r[1] >> 24) as u8 })
}

/// The inactive app partition (where an update goes), or `None` if the flash has no A/B partition table.
pub fn inactive_slot() -> Option<FwSlot> {
    let booted = boot_info()?.partition;
    if booted < 0 {
        return None; // unpartitioned flash (plain UF2 install): no safe place for a second image
    }
    let mut wa = Workarea([0; 4096]);
    let mut loc = [0u32; 2]; // permissions_and_location, permissions_and_flags
    let p = unsafe {
        embassy_rp::rom_data::get_uf2_target_partition(wa.0.as_mut_ptr(), wa.0.len(), FAMILY_RP2350_ARM_S, loc.as_mut_ptr())
    };
    if p < 0 || p == booted as i32 {
        return None;
    }
    let first = loc[0] & LOCATION_SECTOR_BITS;
    let last = (loc[0] >> LOCATION_LAST_SECTOR_LSB) & LOCATION_SECTOR_BITS;
    (last >= first).then(|| FwSlot { offset: first * 4096, size: (last + 1 - first) * 4096 })
}

/// Confirm a trial boot. Returns `None` if nothing was pending, else the ROM result (0 = bought).
pub fn buy_if_pending() -> Option<i32> {
    let info = boot_info()?;
    if info.tbyb_flags & BOOT_TBYB_AND_UPDATE_FLAG_BUY_PENDING == 0 {
        return None;
    }
    let mut wa = Workarea([0; 4096]);
    // The ROM rewrites the image's first flash sector: nothing may run from flash meanwhile.
    Some(cortex_m::interrupt::free(|_| unsafe { embassy_rp::rom_data::explicit_buy(wa.0.as_mut_ptr(), wa.0.len() as u32) }))
}

/// Reboot into the freshly written partition on trial. Does not return on success.
pub fn reboot_into(slot: FwSlot) -> i32 {
    embassy_rp::rom_data::reboot(
        REBOOT2_FLAG_REBOOT_TYPE_FLASH_UPDATE | REBOOT2_FLAG_NO_RETURN_ON_SUCCESS,
        100,
        XIP_BASE + slot.offset,
        0,
    )
}
