"""OPL firmware update: the MCU-side session state machine (reference for firmware/obc-core/src/fwupdate.rs).

The hub streams a new Pico 2 image over the OPL UART into the *inactive* A/B flash partition; the RP2350 bootrom then
boots it on trial ("try before you buy") and falls back to the old partition unless the new image confirms itself.
Spec: docs/design/04-firmware-protocol.md (Firmware update).

Pure logic, no flash access: `chunk()` returns a write plan (sectors to erase, where to program), the firmware executes
it and reports back with `written()`. Stop-and-wait: one FW frame in flight, every FW frame is answered by FW_STATUS.

Image = the flat flash image as linked at 0x10000000 (what the release UF2's rp2350-arm-s blocks carry), `size` bytes
from offset 0, sent strictly in order (the hub fills any gap with 0xFF). Integrity: CRC-32 (IEEE) over those bytes.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from enum import IntEnum

SECTOR = 4096
CHUNK_MAX = 256  # data bytes per FW_CHUNK (one flash page; one UF2 block payload)


class FwState(IntEnum):
    IDLE = 0
    RECEIVING = 1
    DONE = 2  # image complete and verified; the MCU reboots into it


class FwResult(IntEnum):
    OK = 0
    BUSY = 1  # a zone is on: switch every zone off first
    NO_SESSION = 2  # FW_CHUNK / FW_END without FW_BEGIN
    TOO_LARGE = 3  # image larger than the inactive partition
    BAD_OFFSET = 4  # chunk not at next_offset (and not a resend), or past the end of the image
    BAD_CRC = 5  # complete, but CRC-32 mismatch: session dropped
    FLASH_ERROR = 6  # erase/program failed: session dropped
    BAD_PAYLOAD = 7
    NO_PARTITIONS = 8  # flash has no A/B partition table: install it once over USB (firmware/README.md)
    INCOMPLETE = 9  # FW_END before every byte arrived


def crc32(data: bytes, crc: int = 0) -> int:
    """CRC-32/ISO-HDLC (zlib): crc32(b"123456789") == 0xCBF43926. Chainable."""
    return zlib.crc32(data, crc) & 0xFFFFFFFF


# ---- payloads -----------------------------------------------------------------------------------


def fw_begin(size: int, crc: int, version: int) -> bytes:
    return struct.pack("<III", size, crc, version)


def fw_chunk(offset: int, data: bytes) -> bytes:
    return struct.pack("<I", offset) + data


@dataclass(frozen=True)
class FwStatus:
    acked_seq: int
    state: int
    result: int
    next_offset: int
    running_version: int

    FMT = "<BBBII"

    def pack(self) -> bytes:
        return struct.pack(self.FMT, self.acked_seq, self.state, self.result, self.next_offset, self.running_version)

    @classmethod
    def unpack(cls, p: bytes) -> "FwStatus":
        return cls(*struct.unpack(cls.FMT, p))


def version_word(major: int, minor: int, patch: int) -> int:
    """Image version as stored in the IMAGE_DEF VERSION item: (major << 8 | minor) . patch, i.e. 0xMMmmPPPP."""
    return ((major & 0xFF) << 24) | ((minor & 0xFF) << 16) | (patch & 0xFFFF)


# ---- session ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FwSlot:
    """The inactive A/B partition, as a physical flash offset (not an XIP address) and size."""

    offset: int
    size: int


@dataclass(frozen=True)
class FwWrite:
    erase_from: int  # physical; erase [erase_from, erase_to) first, whole sectors (empty = nothing to erase)
    erase_to: int
    addr: int  # physical address to program the chunk's data at


class FwUpdate:
    def __init__(self) -> None:
        self.abort()

    def abort(self) -> None:
        self.state = FwState.IDLE
        self.slot: FwSlot | None = None
        self.size = 0
        self.crc_expected = 0
        self.version = 0
        self.next_offset = 0
        self.erased_to = 0  # image-relative, sector aligned
        self.crc = 0

    @property
    def active(self) -> bool:
        return self.state != FwState.IDLE

    def begin(self, payload: bytes, slot: FwSlot | None, zones_idle: bool) -> FwResult:
        """Start (or restart) a session. `zones_idle`: every zone is off (no setpoint, TEC path open)."""
        if len(payload) != 12:
            return FwResult.BAD_PAYLOAD
        if not zones_idle:
            return FwResult.BUSY
        if slot is None:
            return FwResult.NO_PARTITIONS
        size, crc, version = struct.unpack("<III", payload)
        if size == 0 or size > slot.size:
            self.abort()
            return FwResult.TOO_LARGE
        self.abort()
        self.state, self.slot, self.size, self.crc_expected, self.version = FwState.RECEIVING, slot, size, crc, version
        return FwResult.OK

    def chunk(self, payload: bytes) -> tuple[FwResult, FwWrite | None]:
        """Plan one chunk. (OK, None) = a resend of data already written: nothing to do, answer OK."""
        if self.state != FwState.RECEIVING or self.slot is None:
            return FwResult.NO_SESSION, None
        if len(payload) < 5 or len(payload) > 4 + CHUNK_MAX:
            return FwResult.BAD_PAYLOAD, None
        (offset,) = struct.unpack_from("<I", payload)
        end = offset + len(payload) - 4
        if end <= self.next_offset:
            return FwResult.OK, None  # our status got lost and the hub resent it
        if offset != self.next_offset or end > self.size:
            return FwResult.BAD_OFFSET, None
        need = -(-end // SECTOR) * SECTOR
        erase_to = max(self.erased_to, need)
        return FwResult.OK, FwWrite(self.slot.offset + self.erased_to, self.slot.offset + erase_to, self.slot.offset + offset)

    def written(self, payload: bytes, ok: bool) -> FwResult:
        """Report the outcome of the plan returned by `chunk(payload)`."""
        if not ok:
            self.abort()
            return FwResult.FLASH_ERROR
        (offset,) = struct.unpack_from("<I", payload)
        data = payload[4:]
        self.crc = crc32(data, self.crc)
        self.next_offset = offset + len(data)
        self.erased_to = max(self.erased_to, -(-self.next_offset // SECTOR) * SECTOR)
        return FwResult.OK

    def end(self) -> FwResult:
        if self.state == FwState.DONE:
            return FwResult.OK  # resent FW_END
        if self.state != FwState.RECEIVING:
            return FwResult.NO_SESSION
        if self.next_offset != self.size:
            return FwResult.INCOMPLETE
        if self.crc != self.crc_expected:
            self.abort()
            return FwResult.BAD_CRC
        self.state = FwState.DONE
        return FwResult.OK

    def status(self, acked_seq: int, result: FwResult, running_version: int) -> FwStatus:
        return FwStatus(acked_seq, int(self.state), int(result), self.next_offset, running_version)
