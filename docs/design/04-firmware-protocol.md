# OPL — Open Peltier Link

Wire protocol between the hub computer and (a) the safety MCU over UART and (b) the cover sensor MCU over RS-485.
Our own design. Reference implementation with tests: `software/opod/src/opod/protocol.py`.

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
| `0x80 TELEMETRY` | mcu→host | uptime:u32 t_amb:i16 level:u8 + 2× side block | 2 Hz. Side block: t_water, t_hot, target, tec_mA (i16, >0 cool, **per TEC**; the zone total is n_tec × tec_mA), flow_mL/min (u16), fan %, mode, faults (u16) |
| `0x81 FAULT` | mcu→host | side:u8 faults:u16 | Sent immediately on any change in the fault set. |
| `0x90 SENSOR_BLOCK` | cover→host | side, first_sample:u32, rate_hz:u16, n_ch, n_samples, i16 samples interleaved, n_cap + u16 cap values | 10 Hz × 50 samples |
| `0xF0 ACK` | both | acked_seq:u8 status:u8 | status 0 = ok |

Fault bits (u16): 0 water over-temp, 1 water under-temp, 2 hot-face over-temp, 3 no flow, 4 leak,
5 sensor invalid, 6 host timeout, 7 low water, 8 TEC driver comm (firmware-only). Bits 0, 2, 4 and 5 latch.

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
- Firmware update: the host flashes the MCU over SWD (Raspberry Pi GPIO + OpenOCD) or through a UART
  bootloader. A signed image is optional, since the owner controls the whole stack.

Versioning: bump `VERSION` for incompatible changes. Receivers reject unknown versions.
