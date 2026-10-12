# Build guide: prototype 0 (Solo Starter)

This guide walks you through building the **first Open Bed Climate prototype**: the
[Solo Starter](../../hardware/kits/solo-starter.toml) kit, one zone, three TECs, Tier 0 (off-the-shelf modules only,
no custom PCB, no mains wiring).

> ⚠️ **Nobody has built this yet.** Open Bed Climate is in the design phase. Every number in this guide comes from
> the design documents and the thermal model, not from a working unit. Where the docs leave something open, the
> guide says so. You are the person who finds out what really happens. Please write it down and
> [submit a build report](07-bench-commissioning.md#8-submit-a-build-report).

## Safety first

> ⚠️ **Read [SAFETY.md](../../SAFETY.md) before you buy anything.** This build combines water, ~250 W of DC power
> and, in stage B, a sleeping person.
>
> - **You never wire mains.** Both supplies are certified plug-in bricks with an IEC inlet. Everything you wire is ≤ 24 V DC.
> - **Hardware cutoffs are not optional.** Bimetal cutoffs on every cold plate and heatsink drop the zone relay even if
>   all software fails. You will test them.
> - **Never leave the build running unattended** until it has passed the full commissioning checklist
>   ([step 7](07-bench-commissioning.md)). Stage A exists so that you find problems on a bench, not in a bed.
> - **Have the electrical part reviewed** by a qualified person before you sleep on it.
> - The safety limits (43 °C max setpoint, 45 °C water trip, 75 °C hot-side trip, flow interlock, 10 s heartbeat
>   timeout) are compiled constants in the firmware. This guide never asks you to change them, and neither should you.

## Who this is for

A careful hobbyist who can:

- solder through-hole parts and wires to a module (Pico 2, ADS1115 breakout, relay terminals),
- use a multimeter for voltage, resistance and continuity,
- read a simple schematic and follow a pin table,
- install software from a web page or run a few terminal commands.

You do **not** need to write code, design a PCB or touch mains wiring.

## Two stages

| Stage | What | Thermal load | Goal |
|---|---|---|---|
| **A: bench** | Steps 1–7 | a tube coil in a ~10 L insulated water bath instead of a mat | prove that every safety function works, and **measure** the numbers the model only estimates |
| **B: bed** | Step 8 | the water mat on the bed | first night with conservative limits |

Do not start stage B until every checkbox in stage A is ticked.

## Steps and time

Times are hands-on estimates for a first build. Waiting time (the 24 h leak test, long measurement runs) is listed
separately because you don't need to work during it, but you must stay nearby whenever TECs are powered.

| # | Step | Hands-on | Waiting |
|---|---|---|---|
| 1 | [Tools and safety](01-tools-and-safety.md) | 1 h | — |
| 2 | [Control board](02-control-board.md): Pico 2, ADS1115, NTC dividers, RS-485, relay drivers, fail-safe inputs | 5–7 h | — |
| 3 | [Power path](03-power-path.md): 24 V brick → DPS5020 → fuse → zone relay → polarity relay → TECs | 3–4 h | — |
| 4 | [Thermal stack](04-thermal-stack.md): cold plates, TECs, heatsinks, cutoffs, NTCs | 3–4 h | paste cure per datasheet |
| 5 | [Water loop](05-water-loop.md): reservoir, pump, flow sensor, bench bath, leak test | 3 h | **24 h** leak test |
| 6 | [Software](06-software.md): flash the Pico 2, install the hub, adopt in Home Assistant | 1–2 h | — |
| 7 | [Bench commissioning and measurements](07-bench-commissioning.md) | 4–6 h | 1–2 days of attended measurement runs |
| 8 | [Bed stage](08-bed-stage.md) | 3–4 h | **24 h** mat leak test, first night |
| | **Total** | **≈ 23–31 h** | **≈ 4–5 days elapsed** |

## Parts

The shopping list is [hardware/shopping/solo-starter.md](../../hardware/shopping/solo-starter.md). This guide refers to
parts by their **role id** from [`hardware/parts.toml`](../../hardware/parts.toml) (for example `tec_drive`,
`thermal_cutoff`), because the role says what a part must do and the examples change. Small parts without a role
(resistors, transistors, fittings, wire) are named generically and marked *(no role yet)*.

Roles used in this build:

| Module | Role ids |
|---|---|
| Power | `tec_psu` (24 V, 280 W), `aux_psu` (12 V, 80 W), `tec_drive` (DPS5020), `polarity_relay` (zone relay + DPDT polarity relay + 20 A fuse) |
| Control | `control_mcu` (Pico 2), `hub_controller` (ESP32-S3), `temp_sensors`, `thermal_cutoff`, `leak_sensor` |
| Thermal | `tec_module` ×3, `cold_plate` ×3, `heatsink`, `pump`, `flow_sensor`, `reservoir` |
| Water mat (stage B) | `water_mat`, `quick_disconnect` |
| Sensing (optional, later) | `bcg_sensing` (Solo Starter default: load cells). Not covered in this guide: it doesn't affect the thermal or safety path. |

## Reference documents

The guide follows these documents. If the guide and a document disagree, the document wins, and please open an issue.

- [`hardware/WIRING.md`](../../hardware/WIRING.md): pin map, bring-up order (written for Duo Standard; this guide adapts it to one zone)
- [`firmware/obc-pico2/src/board.rs`](../../firmware/obc-pico2/src/board.rs): pin map source of truth, kit constants
- [`docs/design/01-thermal-fluidics.md`](../design/01-thermal-fluidics.md), [`02-electrical-safety.md`](../design/02-electrical-safety.md), [`04-firmware-protocol.md`](../design/04-firmware-protocol.md)
- [`hub/esphome/README.md`](../../hub/esphome/README.md): what the hub shows in Home Assistant

## Known gaps (read before you start)

These are open in the design and affect a Solo build. Each step repeats the relevant one.

1. **Use the Solo Starter firmware.** The control firmware is built per kit. The `solo-starter` build sets 3 TECs ×
   5.0 A and makes zone 1 inert (outputs held low, no Modbus traffic, no faults). Another kit's build would set the DPS
   to 18 A, which is 6 A per TEC on your 3 TECs. The hub image still has both sides: hide the "Right" entities in Home
   Assistant ([step 6](06-software.md)).
2. **One heatsink sensor in software.** The firmware reads one water NTC and one hot-side NTC per zone; extra sensors
   per cold plate are planned (`temp_sensors` role). The bimetal cutoffs on every plate and heatsink are your per-TEC
   protection.
3. **Unverified parts.** The DPS5020 register map, current scaling and output ripple are unverified on real hardware.
   The reservoir level sensor has no tested example yet. Thermal-cutoff examples are listings without UL. You will
   check these on the bench.
