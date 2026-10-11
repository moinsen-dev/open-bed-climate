# Electrical Design & Safety

This device puts water and several hundred watts next to a sleeping person. Safety is a design input, not an
afterthought. **Do not build or sleep on a prototype without a qualified review** of the mains section and leak handling.

## Power
- Mains is handled only by **off-the-shelf certified supplies** (IEC/EN 62368-1 + UL, PFC, OVP/OCP/OTP). No custom mains PCB.
  - **Tier 0:** one 24 V desktop supply with an IEC inlet per zone (≥ 280 W) for the TECs, plus one 12 V IEC-inlet supply
    for pumps, fans and electronics. No ≥ 600 W supply with an IEC inlet was found (Oct 2026), so we split the load.
  - **Tier 1:** one 24 V ≈ 750 W enclosed supply (terminal-block input) in a pre-assembled, closed power module.
- **Why 24 V:** the TEC driver is a buck converter, and TECs in parallel need ~10–12 V at 4.5–5 A each, more than a
  buck can reliably make from 12 V.
- Everything we design runs on SELV (≤ 24 V).
- **Tier 0 TEC drive:** one programmable CC/CV buck module per zone (DPS5020 class, Modbus RTU from the Pico 2) →
  DC fuse → zone relay (coil through the thermal cutoffs) → DPDT polarity relay → 3–4 TECs in parallel.
  The control MCU writes the current setpoint and the driver's current limit (zone total = TECs × per-TEC cap).
  **That limit is software (Modbus), not a backstop:** a misprogrammed or failed driver could put up to ~21 V on
  TECs rated 14.4 V. The real backstops are the zone relay, which sits **between the driver and the TECs** so a cutoff
  removes power, the per-zone DC fuse, and the supply's overcurrent protection. The polarity relay switches only at
  zero current (2 s dead time in the firmware).
- Power board:
  - Tier 1: 6 TEC channels (3 per side). Each is a synchronous buck stage plus an H-bridge for polarity, with current
    sensing, run as **current-controlled DC, not raw PWM**. PWM ripple through a TEC reduces COP and stresses it.
  - Per-side input protection sized for ~12 A at 24 V (≈ 250 W/side): a hot-swap / eFuse **controller with external
    MOSFETs** (LM5069 / LTC4282 class) plus a per-side contactor-grade relay. Monolithic eFuse ICs are rated in single-digit
    amps and are only suitable for the pump, fan and sensor-board rails.
  - Pump and fan drivers with tach inputs.
- Cover umbilical: 12 V at ≤ 1 A for the sensor board via its own eFuse/polyfuse, plus RS-485. No TEC power or
  mains in the cover.

## Layers of protection

| Hazard | Layer 1 (firmware, `opod.control`) | Layer 2 (hardware, independent of MCU) |
|---|---|---|
| Water too hot (burns) | trip at 45 °C water, latching; heating current tapers above ~37 °C so the TEC water-side face stays ≤ ~45 °C (`heat_limit`, verified in `test_heating_to_cap_keeps_tec_face_below_hardware_cutoff`) | bimetal thermal cutoff on each cold-plate block, opening at 50 °C |
| TEC hot face too hot | trip at 75 °C, latching | 80 °C bimetal on the heatsink base |
| Overcooling | trip at 8 °C | — (not a burn hazard; condensation is handled mechanically) |
| Leak | float/rope sensor in the hub tray + cover edge → TECs and pump off | drip tray, electronics mounted above the water level, IP-rated separation between wet and dry compartments |
| Pump stall | flow interlock: TEC current held at 0 until flow ≥ 0.15 L/min; `NO_FLOW` fault after 20 s | — |
| Host crash | heartbeat timeout 10 s → SAFE | MCU watchdog (independent clock) |
| MCU crash | — | hardware watchdog drops TEC enable (enable line defaults low via pull-down) |
| Sensor open/short | `SENSOR_INVALID`, latching | dual NTC per cold plate (plausibility check) |
| Overcurrent | current loop limit | hot-swap controller + PSU OCP |

Rules:
0. **Cutoffs never sit in the 20 A load path.** Bimetal cutoffs and the watchdog act on the coil of the per-side relay and on the
   TEC-driver enable lines (low-current signals). The relay contacts switch the load.
1. Every TEC enable path is a **fail-off** signal: pulled low, actively driven high, gated by watchdog and cutoffs.
2. Latching faults need an explicit clear from the host, and the host requires a user action to clear.
3. Max skin-contact temperature: the 43 °C setpoint cap comes from low-temperature-burn guidance for prolonged
   contact. Do not raise it.

## Condensation
Below the room dew point (often 12–16 °C), cold plates and cover lines sweat. Insulate the cold plates and
supply lines, put a condensate path into the drip tray, and add a humidity/dew-point check on the hub. The setpoint
should never go below dew point + 1 K when cooling below 16 °C. **`opod-core` on the hub enforces this**,
because the SHT4x is read there (implemented in the ESPHome hub: `room_temperature` / `room_humidity`).
The MCU only enforces the fixed 13 °C floor.

## Compliance path (if this ever ships beyond DIY)
IEC 60335-1 / -2-17 (blankets, pads and flexible heating appliances for warming the bed) is the most relevant
household standard. EN 62368-1 applies to the PSU. Radio: RED (EU) / FCC Part 15 is covered by using a
pre-certified Wi-Fi/BLE module, which the Raspberry Pi's module is.
