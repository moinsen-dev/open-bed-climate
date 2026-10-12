"""OPL: the Open Peltier Link between hub computer and real-time MCU (and cover sensor MCU).

Own design, not derived from any vendor protocol. Spec: docs/design/04-firmware-protocol.md

Wire format per frame:  COBS( header | payload | crc16 ) 0x00
  header  = version:u8  seq:u8  type:u8
  crc16   = CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) over header+payload, little-endian
All multi-byte integers are little-endian. Temperatures are centi-degC (i16).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum

VERSION = 1


class MsgType(IntEnum):
    HEARTBEAT = 0x01  # host -> mcu, empty payload
    SET_TARGET = 0x10  # host -> mcu: side:u8 enable:u8 centi_c:i16
    CLEAR_FAULTS = 0x11  # host -> mcu: side:u8
    PRIME = 0x12  # host -> mcu: empty
    FW_BEGIN = 0x20  # host -> mcu: size:u32 crc32:u32 version:u32 (see fwupdate.py)
    FW_CHUNK = 0x21  # host -> mcu: offset:u32 data[1..256]
    FW_END = 0x22  # host -> mcu: empty; verify, then reboot into the new image
    FW_ABORT = 0x23  # host -> mcu: empty
    FW_QUERY = 0x24  # host -> mcu: empty; answered with FW_STATUS
    TELEMETRY = 0x80  # mcu -> host, see Telemetry
    FAULT = 0x81  # mcu -> host: side:u8 faults:u16
    FW_STATUS = 0x82  # mcu -> host: answer to every FW_* frame, see fwupdate.FwStatus
    SENSOR_BLOCK = 0x90  # cover -> host, see SensorBlock
    ACK = 0xF0  # either way: acked_seq:u8 status:u8


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def cobs_encode(data: bytes) -> bytes:
    out = bytearray()
    block = bytearray()
    for b in data:
        if b == 0:
            out.append(len(block) + 1)
            out += block
            block.clear()
        else:
            block.append(b)
            if len(block) == 254:
                out.append(255)
                out += block
                block.clear()
    out.append(len(block) + 1)
    out += block
    return bytes(out)


def cobs_decode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        code = data[i]
        if code == 0:
            raise ValueError("zero byte inside COBS frame")
        end = i + code
        if end > len(data):
            raise ValueError("truncated COBS frame")
        out += data[i + 1 : end]
        i = end
        if code < 255 and i < len(data):
            out.append(0)
    return bytes(out)


@dataclass(frozen=True)
class Frame:
    seq: int
    type: MsgType
    payload: bytes = b""


def encode(frame: Frame) -> bytes:
    body = struct.pack("<BBB", VERSION, frame.seq & 0xFF, frame.type) + frame.payload
    body += struct.pack("<H", crc16_ccitt_false(body))
    return cobs_encode(body) + b"\x00"


def decode(wire: bytes) -> Frame:
    """Decode one frame (with or without trailing 0x00)."""
    body = cobs_decode(wire.rstrip(b"\x00"))
    if len(body) < 5:
        raise ValueError("frame too short")
    (crc,) = struct.unpack("<H", body[-2:])
    if crc != crc16_ccitt_false(body[:-2]):
        raise ValueError("bad crc")
    version, seq, typ = struct.unpack("<BBB", body[:3])
    if version != VERSION:
        raise ValueError(f"unsupported version {version}")
    return Frame(seq, MsgType(typ), body[3:-2])


class StreamDecoder:
    """Feed arbitrary byte chunks from a UART; yields complete valid frames, drops corrupt ones."""

    def __init__(self) -> None:
        self._buf = bytearray()
        self.errors = 0

    def feed(self, chunk: bytes) -> list[Frame]:
        frames = []
        self._buf += chunk
        while (idx := self._buf.find(0)) != -1:
            raw = bytes(self._buf[:idx])
            del self._buf[: idx + 1]
            if not raw:
                continue
            try:
                frames.append(decode(raw))
            except ValueError:
                self.errors += 1
        return frames


# ---- typed payloads -------------------------------------------------------


def set_target(side: int, centi_c: int | None) -> bytes:
    return struct.pack("<BBh", side, 0 if centi_c is None else 1, centi_c or 0)


def parse_set_target(p: bytes) -> tuple[int, int | None]:
    side, en, c = struct.unpack("<BBh", p)
    return side, (c if en else None)


@dataclass(frozen=True)
class SideTelemetry:
    t_water: int  # centi-degC, i16; -32768 = invalid
    t_hot_face: int
    target: int  # centi-degC, -32768 = off
    tec_ma: int  # i16, signed: >0 cooling; per TEC (zone total = n_tec * tec_ma, which is what the driver is set to)
    flow_mlpm: int  # u16
    fan_pct: int  # u8
    mode: int  # u8
    faults: int  # u16

    FMT = "<hhhhHBBH"


@dataclass(frozen=True)
class Telemetry:
    uptime_ms: int  # u32
    t_ambient: int  # centi-degC
    water_level_pct: int  # u8
    sides: tuple[SideTelemetry, SideTelemetry]

    def pack(self) -> bytes:
        out = struct.pack("<IhB", self.uptime_ms, self.t_ambient, self.water_level_pct)
        for s in self.sides:
            out += struct.pack(SideTelemetry.FMT, s.t_water, s.t_hot_face, s.target, s.tec_ma, s.flow_mlpm, s.fan_pct, s.mode, s.faults)
        return out

    @classmethod
    def unpack(cls, p: bytes) -> "Telemetry":
        up, amb, lvl = struct.unpack_from("<IhB", p, 0)
        off = struct.calcsize("<IhB")
        n = struct.calcsize(SideTelemetry.FMT)
        sides = tuple(SideTelemetry(*struct.unpack_from(SideTelemetry.FMT, p, off + k * n)) for k in range(2))
        return cls(up, amb, lvl, sides)  # type: ignore[arg-type]


@dataclass(frozen=True)
class SensorBlock:
    """Cover sensor batch: N piezo channels sampled synchronously, plus capacitance.

    Layout: side:u8 first_sample_idx:u32 rate_hz:u16 n_ch:u8 n_samples:u8
            piezo i16[n_samples][n_ch] (interleaved) cap u16[n_cap] with n_cap:u8 prefix
    """

    side: int
    first_sample: int
    rate_hz: int
    piezo: tuple[tuple[int, ...], ...]  # [sample][channel]
    cap: tuple[int, ...]

    def pack(self) -> bytes:
        n_ch = len(self.piezo[0]) if self.piezo else 0
        out = struct.pack("<BIHBB", self.side, self.first_sample, self.rate_hz, n_ch, len(self.piezo))
        for row in self.piezo:
            out += struct.pack(f"<{n_ch}h", *row)
        out += struct.pack(f"<B{len(self.cap)}H", len(self.cap), *self.cap)
        return out

    @classmethod
    def unpack(cls, p: bytes) -> "SensorBlock":
        side, first, rate, n_ch, n_s = struct.unpack_from("<BIHBB", p, 0)
        off = struct.calcsize("<BIHBB")
        rows = []
        for _ in range(n_s):
            rows.append(struct.unpack_from(f"<{n_ch}h", p, off))
            off += 2 * n_ch
        (n_cap,) = struct.unpack_from("<B", p, off)
        cap = struct.unpack_from(f"<{n_cap}H", p, off + 1)
        return cls(side, first, rate, tuple(rows), cap)
