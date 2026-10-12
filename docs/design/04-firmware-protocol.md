# OPL — Open Peltier Link

Wire protocol between the hub computer and (a) the safety MCU over UART and (b) the cover sensor MCU over RS-485.
Our own design. Reference implementation with tests: `software/obc/src/obc/protocol.py`.

## Framing
```
wire  = COBS(body) 0x00
body  = version:u8 | seq:u8 | type:u8 | payload | crc16:u16le
crc16 = CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) over version..payload
```
- COBS + 0x00 delimiter: a receiver resyncs at the next zero, so a corrupt frame costs only itself.
- Little-endian everywhere. Temperatures are i16 centi-°C; `-32768` means invalid/off.
- `seq` increments per sender. Commands are answered with `ACK(acked_seq, status)`.

## Messages
| Type | Dir | Payload | Notes |
|---|---|---|---|
| `0x01 HEARTBEAT` | host→mcu | — | ≥ 1 Hz. No heartbeat for 10 s → MCU raises `HOST_TIMEOUT` and goes SAFE. |
| `0x10 SET_TARGET` | host→mcu | side:u8 enable:u8 centi_c:i16 | MCU clamps to 13–43 °C. enable=0 turns the side off. |
| `0x11 CLEAR_FAULTS` | host→mcu | side:u8 | Only sent after a user action. |
| `0x12 PRIME` | host→mcu | — | Pump-only purge cycle. |
| `0x20 FW_BEGIN` | host→mcu | size:u32 crc32:u32 version:u32 | Start a firmware update (see below). |
| `0x21 FW_CHUNK` | host→mcu | offset:u32 data[1..256] | Next image bytes, strictly in order. |
| `0x22 FW_END` | host→mcu | — | Verify, then reboot into the new image on trial. |
| `0x23 FW_ABORT` | host→mcu | — | Drop the session. |
| `0x24 FW_QUERY` | host→mcu | — | Ask for `FW_STATUS` (e.g. the running version after the reboot). |
| `0x80 TELEMETRY` | mcu→host | uptime:u32 t_amb:i16 level:u8 + 2× side block | 2 Hz. Side block: t_water, t_hot, target, tec_mA (i16, >0 cool, **per TEC**; the zone total is n_tec × tec_mA), flow_mL/min (u16), fan %, mode, faults (u16) |
| `0x81 FAULT` | mcu→host | side:u8 faults:u16 | Sent immediately on any change in the fault set. |
| `0x82 FW_STATUS` | mcu→host | acked_seq:u8 state:u8 result:u8 next_offset:u32 running_version:u32 | Answer to every `FW_*` frame (instead of `ACK`). |
| `0x90 SENSOR_BLOCK` | cover→host | side, first_sample:u32, rate_hz:u16, n_ch, n_samples, i16 samples interleaved, n_cap + u16 cap values | 10 Hz × 50 samples |
| `0xF0 ACK` | both | acked_seq:u8 status:u8 | status 0 = ok |

Fault bits (u16): 0 water over-temp, 1 water under-temp, 2 hot-face over-temp, 3 no flow, 4 leak,
5 sensor invalid, 6 host timeout, 7 low water, 8 TEC driver comm (firmware-only), 9 fan stalled (firmware-only,
needs a fan tach signal, which the Tier 0 carrier doesn't have). Bits 0, 2, 4 and 5 latch.

## Links
- Hub ↔ safety MCU: 3.3 V UART at 460800 baud, on-board.
- Hub ↔ cover: half-duplex RS-485 at 921600 baud, with the cover as streaming master during sampling.
  Sensor data is about 20 kB/s, so the link runs at about 20 % load (asserted < 25 % in the tests).

## MCU firmware structure (implemented in Rust: [`firmware/`](../../firmware))
- Tier 1 only: 1 kHz current loops for the TEC channels on the power board.
- 10 Hz with measured dt: supervisor, then PID per zone → per-TEC current, heating taper, flow interlock (no TEC
  current until flow ≥ 0.15 L/min), polarity dead time. Telemetry at 2 Hz. Golden vectors from the Python reference
  keep the two implementations identical.
- Tier 0 TEC drivers: Modbus RTU to one DPS-class buck module per zone (current setpoint, output enable, read-back of
  V/I). Polarity relay GPIO switches only after a read-back confirms zero output current (`POLARITY_DEADTIME_S`).
- Independent watchdog. TEC enable outputs default low.
- Fans and pumps: 25 kHz PWM on their low-side switches. Duty comes from `obc-core::cooling` (reference:
  `software/obc/src/obc/cooling.py`, golden vectors): fan = max(controller request, hot-face curve 32→55 °C) with
  on/off and 2 K falling-edge hysteresis, 25 % minimum, 1 s kick at 100 % on every start, run-on while the hot face is
  still warm; pump = 100 % while priming, for 5 s after a start, in SAFE and whenever flow is below 0.15 L/min (then
  held 30 s), else the board's run duty (≥ 50 %); 0 on leak or low water. The flow interlock and `NO_FLOW` stay in the
  supervisor, so a slow pump still cuts the TECs.
- Firmware update: over OPL from the hub (below), or over USB (BOOTSEL / picotool) or SWD.

## Firmware update over OPL

> **Untested on hardware.** The protocol, the session logic and the hub sender are host-tested (Python reference,
> Rust golden replay, C++ sender against a simulated MCU with a lossy link). The RP2350 bootrom calls (A/B partitions,
> try-before-you-buy) follow the datasheet and pico-sdk headers but have never run.

**How it works**
1. The Pico's flash carries an A/B partition table (`firmware/obc-pico2/partitions.json`). It is installed once over USB.
2. The hub sends `FW_QUERY` to learn the running version, then `FW_BEGIN(size, crc32, version)`. The MCU refuses with `BUSY` unless every zone is off, and with
   `NO_PARTITIONS` on flash without the table. While a session is open, it rejects every non-off `SET_TARGET` and
   `PRIME`, so the TECs stay off until the reboot.
3. `FW_CHUNK(offset, ≤ 256 bytes)` frames go strictly in order into the **inactive** partition, the one the bootrom
   names for a UF2 of family rp2350-arm-s. Each sector is erased before it is first written.
4. `FW_END`: if every byte arrived and the CRC-32 (zlib/IEEE) of the image matches, the MCU answers `state = DONE`.
   It then reboots with a bootrom FLASH_UPDATE reboot into the new partition.
5. Release images (built with the `tbyb` feature) are flagged *try before you buy* in their IMAGE_DEF.
   - The new firmware confirms itself (`explicit_buy`) after 5 s of a clean control loop.
   - Confirming also erases the first sector of the old partition, so the new image stays the boot image.
   - If the new firmware crashes or resets before it confirms, the bootrom boots the previous partition again.
6. The hub sends `FW_QUERY` after about 8 s and compares `running_version` with the new image's version and the
   old one. The answer to `FW_END` can get lost while the MCU reboots. Then the resent `FW_END` reaches the new image,
   which answers `NO_SESSION`, and the hub goes on to the version check.

**Transfer rules**
- **Stop-and-wait:** one `FW_*` frame in flight, and the hub sends nothing else (no heartbeat, no targets) until its
  `FW_STATUS` arrives. The MCU masks interrupts while it erases or programs flash, so bytes arriving then would be lost.
- **Timeouts and resends:** the hub resends after 2 s, up to 5 times.
  - A resent chunk the MCU already has is answered `OK` and not written again.
  - Any other offset gets `BAD_OFFSET` together with `next_offset`, and the hub resumes from there.
- **Status codes:** `result` is one of 0 ok, 1 busy (a zone is on), 2 no session, 3 too large, 4 bad offset, 5 bad
  CRC, 6 flash error, 7 bad payload, 8 no partition table, 9 incomplete. `state` is 0 idle, 1 receiving, 2 done.
- **Image format:** the flat image as linked at 0x10000000, i.e. the payload of the release UF2's rp2350-arm-s blocks.
  The hub converts the UF2 itself, skips the RP2350-E10 absolute block and fills any gap with 0xFF.
- **Session timeout:** the MCU drops an open session after 30 s without a `FW_*` frame (hub reboot, lost
  `FW_ABORT`), so the zones never stay locked off.
- **Version:** `version` is the IMAGE_DEF VERSION word `0xMMmmPPPP` (major, minor, patch of the obc-pico2 crate).
  - Without TBYB, the bootrom boots the partition with the higher version.
  - With TBYB, the confirmed image wins even at an equal version.
  - Releases should still raise the crate version. Otherwise the hub can't tell a successful switch from a rollback,
    and it logs the update as unverified.
- **When updates are allowed:** the Pico has no wall clock, so the rule "not at night" lives on the hub. The hub
  refuses while any zone is on. `force` switches every zone off first, and the zones come back with the next 10 s
  target resend.

Versioning: bump `VERSION` for incompatible changes. Receivers reject unknown versions.
