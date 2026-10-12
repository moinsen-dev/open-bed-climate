# Open Bed Climate firmware

| Crate | What | Runs on |
|---|---|---|
| [`obc-core`](obc-core) | zone controller + safety supervisor, fan/pump duty, OPL protocol + firmware-update session, Modbus frames for DPS-class TEC drivers, NTC conversion. `no_std`, no allocation, no clock access. | anywhere (host-tested) |
| [`obc-pico2`](obc-pico2) | control firmware for the Raspberry Pi Pico 2 (RP2350) on the Tier 0 board, built with [embassy](https://embassy.dev) | Pico 2 |

**Status:** `obc-core` matches the Python reference (golden vectors, see below). `obc-pico2` compiles
(~50 KB flash, ~7.6 KB RAM) but **has not run on hardware yet**. Bring it up with the order in
[`hardware/WIRING.md`](../hardware/WIRING.md).

## Test the core (no hardware needed)

```sh
cd firmware
cargo test            # unit tests + golden-vector replay against the Python model
```

`obc-core/tests/vectors/golden.json` is generated from the Python reference (`cd software/obc && uv run python -m obc.golden`).
The Rust controller must make the same decisions (mode, faults, pump, polarity relay) and produce the same TEC current
(±0.02 A; currently 0.00001 A) in every scenario, and produce byte-identical OPL frames. The fan/pump duties
(`cooling`) and the firmware-update session (`fwupdate`) are replayed the same way. **If you change behaviour,
change the Python reference first, regenerate the vectors, then make Rust pass.** CI checks that the vectors are current.

## Install a release (no toolchain)
Every release has one Pico 2 image per kit: `obc-pico2-solo-starter.uf2`, `obc-pico2-duo-standard.uf2`,
`obc-pico2-duo-reference.uf2` ([releases](https://github.com/moinsen-dev/open-bed-climate/releases), or
<https://openbedclimate.moinsen.dev/install/>). Hold BOOTSEL, plug the Pico 2 in, and drop **your kit's** file on the
`RP2350` drive. The kit sets the zones and the TEC current limit, so another kit's image can overdrive your parts.
Checksums are in `SHA256SUMS`. CI builds them (`.github/workflows/release.yml`, on a `v*` tag) with the prebuilt
`picotool` 2.3.1 (`uf2 convert --family rp2350-arm-s --abs-block`, i.e. with the RP2350-E10 workaround block), and
`tools/check_uf2.py` checks every image before it is published.

## Build and flash the Pico 2 firmware

```sh
rustup target add thumbv8m.main-none-eabihf
cd firmware/obc-pico2
cargo build --release                                                      # Duo Standard (default)
cargo build --release --no-default-features --features kit-solo-starter    # or kit-duo-reference
cargo run --release              # flash + log via a debug probe (probe-rs), see .cargo/config.toml
# or, without a probe: hold BOOTSEL, plug in, then
picotool load -u -v -x -t elf target/thumbv8m.main-none-eabihf/release/obc-pico2
```

## Firmware update over OPL (from the hub)
> **Untested on hardware.** See [04-firmware-protocol.md](../docs/design/04-firmware-protocol.md#firmware-update-over-opl)
> for the protocol and the rules.

**One-time setup, over USB.** The update path needs the RP2350 A/B partition table in flash:
```sh
picotool partition create obc-pico2/partitions.json pt.uf2   # two 2000K app partitions, A and B
# hold BOOTSEL, plug in, drop pt.uf2 (or: picotool load pt.uf2 && picotool reboot -u), then drop your kit's .uf2
```
On flash without the table, the firmware runs as before but answers `FW_BEGIN` with `NO_PARTITIONS`.

**What happens during an update**
- The Pico writes the new image into the inactive partition, verifies its CRC-32 and reboots into it on trial.
- Rollback needs a *try before you buy* image: build with the `tbyb` feature (release builds,
  `--features kit-<kit>,tbyb`).
  - The image confirms itself after 5 s of a clean control loop (`ota::buy_if_pending`). Until then, any reset falls
    back to the previous partition.
  - A TBYB image only boots through a flash-update boot: a UF2 drop or an OPL update. It does **not** boot after a
    plain reset, such as `cargo run` with probe-rs or an SWD flash. That's why the feature is off by default.
  - Check the defmt log for `trial image confirmed`.
- `IMAGE_DEF` carries the crate version (`0xMMmmPPPP`). **Bump `obc-pico2`'s version for every release.**
  - Without TBYB, the bootrom prefers the higher version.
  - With TBYB, the hub needs a version change to confirm that the new image really runs.

**Hub side.** `opl_fw.h` holds the UF2 → image conversion and the `FwSender` state machine. `ObcHub::start_firmware_update(uf2, len, force)`
streams the update and logs progress. It is refused while any zone is on, unless `force`. **Not done yet:**
- fetching the UF2 on the hub (an `http_request` download of `obc-pico2-<kit>.uf2` from the GitHub release, about
  100 KB of RAM);
- a Home Assistant entity to trigger the update and show its progress.

Until then, call `start_firmware_update` from a lambda, or update over USB.

## Configure for your kit
The kit limits come from a Cargo feature (`kit-solo-starter`, `kit-duo-standard` (default), `kit-duo-reference`), one
block per kit in [`obc-pico2/src/board.rs`](obc-pico2/src/board.rs): zones, `TECS_PER_ZONE` and `MAX_TEC_CURRENT_A`
from the kit file. `software/obc/tests/test_kits.py` checks each block against `hardware/kits/<kit>.toml`. For your
own kit, add a TOML, a feature and a block. On a 1-zone kit, zone 1 is inert: its outputs stay low, its driver is never
addressed, it reports no faults, its telemetry side is off with no temperatures, and any non-off target is rejected.
Also in `board.rs`: the NTC calibration, the flow-sensor factor, the pump run duty (`PUMP_RUN_DUTY`), and the TEC driver register map (`DPS_MAP`: **verify
it against your module's protocol document**). The safety limits are not in this file; they are constants in
`obc-core::control` and need a safety review to change (see [SAFETY.md](../SAFETY.md)).

## Design notes
- Control loop at 10 Hz with the measured `dt`. The supervisor runs every cycle.
- Hardware watchdog with a 1 s timeout. All outputs start low; relay drivers need pull-downs (see WIRING.md).
- Time is `f64` seconds; tested with a one-year uptime offset. Flow is computed over the measured window.
- TEC driver sequencing is a host-tested state machine (`obc-core::driver`), with at most one Modbus transaction
  per zone per cycle:
  - The voltage ceiling is written once and re-verified every 60 s.
  - Current is written on change: decreases immediately, increases at most once per second.
  - The output is only enabled when the held setpoint is not higher than requested.
  - The polarity relay switches only after output off + a < 0.1 A read-back.
  - 3 failed transactions open the zone relay and set fault bit 8 (`DRIVER_COMM`, firmware-only).
- Modbus: RX is drained before each request, and the RS-485 driver is released only after the UART BUSY flag clears.
- Inputs are fail-safe: a broken leak or level wire reads as a fault.
- Fans and pumps: 25 kHz PWM on the carrier's low-side switches (pump = channel A, fan = channel B of one PWM slice
  per zone), duty from `obc-core::cooling`.
  - Fan: hot-face curve with hysteresis, a minimum duty, a kick-start, and run-on after the TECs stop.
  - Pump: full speed while priming, at start, in SAFE and on low flow.
  - The carrier routes no 4-pin PWM wire and no tach input, so stall detection (fault bit 9, which cuts the TECs) is
    implemented and tested but fed `None`.

## Help wanted
- First hardware bring-up and a logic-analyser trace of the Modbus traffic
- Fan tach input (needs a carrier revision) and D5 pump PWM input
- First real run of the OPL firmware update (A/B partitions, trial boot, rollback), and the hub-side UF2 download
- ESPHome external component for the hub side of OPL
