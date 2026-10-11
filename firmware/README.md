# Open Bed Climate firmware

| Crate | What | Runs on |
|---|---|---|
| [`opod-core`](opod-core) | zone controller + safety supervisor, OPL protocol, Modbus frames for DPS-class TEC drivers, NTC conversion. `no_std`, no allocation, no clock access. | anywhere (host-tested) |
| [`opod-pico2`](opod-pico2) | control firmware for the Raspberry Pi Pico 2 (RP2350) on the Tier 0 board, built with [embassy](https://embassy.dev) | Pico 2 |

**Status:** `opod-core` matches the Python reference (golden vectors, see below). `opod-pico2` compiles
(~50 KB flash, ~7.6 KB RAM) but **has not run on hardware yet**. Bring it up with the order in
[`hardware/WIRING.md`](../hardware/WIRING.md).

## Test the core (no hardware needed)

```sh
cd firmware
cargo test            # unit tests + golden-vector replay against the Python model
```

`opod-core/tests/vectors/golden.json` is generated from the Python reference (`cd software/opod && uv run python -m opod.golden`).
The Rust controller must make the same decisions (mode, faults, pump, polarity relay) and produce the same TEC current
(±0.02 A; currently 0.00001 A) in every scenario, and produce byte-identical OPL frames. **If you change behaviour,
change the Python reference first, regenerate the vectors, then make Rust pass.** CI checks that the vectors are current.

## Build and flash the Pico 2 firmware

```sh
rustup target add thumbv8m.main-none-eabihf
cd firmware/opod-pico2
cargo build --release
cargo run --release              # flash + log via a debug probe (probe-rs), see .cargo/config.toml
# or, without a probe: hold BOOTSEL, plug in, then
picotool load -u -v -x -t elf target/thumbv8m.main-none-eabihf/release/opod-pico2
```

## Configure for your kit
Edit [`opod-pico2/src/board.rs`](opod-pico2/src/board.rs): `MAX_TEC_CURRENT_A` and `TECS_PER_ZONE` from your kit file,
the NTC calibration, the flow-sensor factor, and the TEC driver register map (`DPS_MAP`: **verify it against your
module's protocol document**). The safety limits are not in this file; they are constants in `opod-core::control`
and need a safety review to change (see [SAFETY.md](../SAFETY.md)).

## Design notes
- Control loop at 10 Hz with the measured `dt`. The supervisor runs every cycle.
- Hardware watchdog with a 1 s timeout. All outputs start low; relay drivers need pull-downs (see WIRING.md).
- Time is `f64` seconds; tested with a one-year uptime offset. Flow is computed over the measured window.
- TEC driver sequencing is a host-tested state machine (`opod-core::driver`), with at most one Modbus transaction
  per zone per cycle:
  - The voltage ceiling is written once and re-verified every 60 s.
  - Current is written on change: decreases immediately, increases at most once per second.
  - The output is only enabled when the held setpoint is not higher than requested.
  - The polarity relay switches only after output off + a < 0.1 A read-back.
  - 3 failed transactions open the zone relay and set fault bit 8 (`DRIVER_COMM`, firmware-only).
- Modbus: RX is drained before each request, and the RS-485 driver is released only after the UART BUSY flag clears.
- Inputs are fail-safe: a broken leak or level wire reads as a fault.

## Help wanted
- First hardware bring-up and a logic-analyser trace of the Modbus traffic
- Fan and pump PWM (currently on/off), D5 pump PWM input
- OPL firmware update path from the hub (UART bootloader)
- ESPHome external component for the hub side of OPL
