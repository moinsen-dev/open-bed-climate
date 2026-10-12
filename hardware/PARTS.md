# Parts catalog

<!-- GENERATED from parts.toml by `python -m obc.render_parts`. Edit parts.toml, not this file. -->

Roles first, then example parts. **Safety-relevant** roles (🛡) affect the limits in [SAFETY.md](../SAFETY.md).
Status: ✅ key specs confirmed in the datasheet · 🟡 only seen in a listing · ❔ please verify · ❌ checked and rejected.
Found a better or local part? Open a *Part substitution* issue or edit `parts.toml`.

## `tec_psu` 🛡 · Power

**Requirement:** Certified (IEC/EN/UL 62368-1), active PFC, 24 V, ≥ 280 W per zone. The builder must never wire mains: IEC C14 inlet or molded mains cord only.

24 V because the TEC driver is a buck converter: TECs need ~11.5 V at 5 A, so a 12 V input is too low. Big 600–750 W units (Mean Well RSP-750, UHP-750) have mains screw terminals and are only allowed inside a pre-assembled, closed power module (Tier 1).

| Example | Status | Notes |
|---|---|---|
| [Mean Well GST280A24-C6P (desktop, IEC C14)](https://www.meanwellusa.com/upload/pdf/GST280A/GST280A-spec.pdf) | ✅ datasheet (2026-10-11) | Confirmed: 24 V / 11.67 A / 280.08 W, 85-264 VAC, PF > 0.95 at 230 VAC (the datasheet gives a PF figure, not the words 'active PFC'), 93 % efficiency, IEC320-C14 inlet, output plug C6P = Molex 39-01-2060 equivalent (6-pin). Safety: UL/CSA/EN/IEC 62368-1. One unit per zone (280 W covers ~18 A at ~11.5 V through the buck with margin). |
| [Mean Well RSP-750-24 inside a closed power module (C14 + fuse + switch)](https://www.meanwell.com/Upload/PDF/RSP-750/RSP-750-SPEC.PDF) | ✅ datasheet (2026-10-10) | Tier 1 only. AC input on terminal block TB1, so the mains side must be assembled and tested by a qualified person. Has a fan. |
| [HP common-slot server PSU + breakout board](https://tindie.com/products/gumslone/smart-wifi-server-psu-breakout-board) | ❌ rejected (2026-10-10) | Loud high-RPM fans (bedroom), the certification does not cover the DIY breakout, and pinouts vary by model. |

## `aux_psu` 🛡 · Power

**Requirement:** Certified, 12 V, IEC inlet, sized so the continuous load stays ≤ 80 % of the rating (kit check: 25 W per zone + 15 W shared, i.e. ≥ 50 W for one zone, ≥ 82 W for two). Feeds pumps, fans, control MCU and hub.

| Example | Status | Notes |
|---|---|---|
| [Mean Well GST90A12-P1M (desktop)](https://www.meanwellusa.com/upload/pdf/GST90A/GST90A-spec.pdf) | ✅ datasheet (2026-10-11) | Confirmed: 12 V / 6.67 A / 80 W (not 90 W: the 90 W versions are the 15 V and up models), IEC320-C14 inlet, DC plug P1M (5.5 x 2.5 x 11 mm, center positive), UL/CSA/EN/IEC 62368-1, PF > 0.91 at 230 VAC. Enough for one zone (Solo Starter, 40 W load); too small for two zones (65 W > 80 % of 80 W). |
| [Mean Well GST120A12-R7B (desktop, two-zone kits)](https://www.meanwell.com/productSeries.aspx) | ❔ unverified | Same GST family, 12 V / 120 W class. Confirm current rating, IEC C14 inlet and DC plug in the datasheet. |

## `tec_drive` 🛡 · Power

**Requirement:** Smooth DC, current-controlled (ripple < 10 % of max current), ≥ 18 A per zone (4 TECs in parallel at 4.5 A), controllable from a 3.3 V MCU. Its current limit is set by software, so the per-zone DC fuse and zone relay are required as backstops.

Polarity for heat/cool comes from a DPDT relay (role polarity_relay), switched only at zero current; the firmware enforces a 2 s dead time. Raw PWM is not allowed: it cuts TEC efficiency, and DIY builds that used it ran their capacitors hot.

| Example | Status | Notes |
|---|---|---|
| [DPS5020 programmable buck module (50 V / 20 A, Modbus RTU over UART)](https://tech.scargill.net/dps5020-diy-power-supply/) | 🟡 listing (2026-10-10) | One per zone. Output ≤ ~90 % of input, so it needs the 24 V supply. Output ripple not yet measured: please measure it. Early units had a failed output capacitor. Register map cross-checked against community sources (Scargill thread script, haarer/pyDPS5015): 0x0000 U-set, 0x0001 I-set, 0x0002 U-out, 0x0003 I-out, 0x0009 on/off, 16-bit holding registers; 2 decimals (x100) for voltage and, on the DPS5020, current. The vendor protocol PDF (Ruideng, V1.2) could not be fetched here (bot wall), so function codes 0x03/0x06/0x10 and the exact DPS5020 current scaling are from secondary sources: verify on your unit. Note the second register block at 0x0050+ is stored memory group M0 (U-set/I-set/OVP/OCP/OPP...), not the live setpoint. |
| [Riden RD6012 (60 V / 12 A, Modbus RTU)](https://www.cnx-software.com/2021/12/15/riden-rd6012p-usb-wifi-dc-power-supply-connects-to-your-pc-or-smartphone/) | 🟡 listing (2026-10-10) | 12 A, so it covers 2 TECs in parallel at 5 A (Solo Starter). An ESPHome community config exists. |
| [TI DRV8262 H-bridge + LC filter (TEC mode)](https://www.ti.com/product/DRV8262) | ✅ datasheet (2026-10-10) | Tier 1 power board candidate. The datasheet has TEC guidance (PWM + 2nd-order LC filter, ripple < 10 %). Needs a custom PCB. |
| [Meerstetter TEC-1091 / TEC-1122](https://www.meerstetter.ch/) | ❌ rejected (2026-10-10) | Excellent but far over budget (≈ USD 370–1,600 each, reseller prices); the 1091 is only ±4 A. |

## `polarity_relay` 🛡 · Power

**Requirement:** DPDT, ≥ 20 A contacts at 24 V DC, 12 V coil; plus a per-zone enable relay between TEC driver and TECs whose coil goes through the thermal cutoffs, and a per-zone DC fuse.

| Example | Status | Notes |
|---|---|---|
| [CIT Relay A102CS12VDC (12 V coil, 2 Form C = DPDT, automotive) + per-zone 20 A DC blade fuse](https://atta.szlcsc.com/upload/public/pdf/source/231023/A10-ebfe5758433fce54477dea240fbb29a9.pdf) | ✅ datasheet (2026-10-11) | A10 series datasheet: 2C contacts rated 25 A / 30 A at 14 VDC on NO and 20 A / 25 A at 14 VDC on NC, max switching voltage 28 VDC, limiting continuous current 30/25 A (NO/NC) at 23 C, derated to 25/20 A at 85 C. The relay sits after the buck driver so it never sees 24 V; the voltage ceiling is 14 V (TEC_VOLTAGE_CEILING_V). With 18 A per zone the NC side is marginal at temperature, so wire the load through the NO contacts in both polarities (H-bridge-style: two SPDT relays, or the 2C with the NO pair cross-wired) and switch only at zero current. Datasheet copy is a distributor mirror: confirm against citrelay.com. |
| [American Zettler AZ9891J-2C-12DE (12 V coil, DPDT, 30 A)](https://www.digikey.com/en/products/detail/american-zettler/AZ9891J-2C-12DE/12171586) | 🟡 listing (2026-10-11) | Distributor listing: 30 A contacts, ~67 mA coil, 16 VDC max switching voltage, sealed. DC contact curve not checked; get the manufacturer datasheet before use. |

## `control_mcu` 🛡 · Control

**Requirement:** Runs the Open Bed Climate control firmware (port of obc.control): PID, supervisor, watchdog. Separate from any Wi-Fi/network chip.

| Example | Status | Notes |
|---|---|---|
| [Raspberry Pi Pico 2 (RP2350)](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf) | ✅ datasheet (2026-10-10) | ≈ USD 5. Talks Modbus to the TEC drivers and OPL to the hub. |

## `hub_controller` · Hub

**Requirement:** Wi-Fi, Home Assistant integration, schedules, UI. Can only request setpoints.

| Example | Status | Notes |
|---|---|---|
| [Espressif ESP32-S3-DevKitC-1 with ESPHome](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/index.html) | ✅ datasheet (2026-10-10) | Tier 0 default. The OPL client is an ESPHome external component (local C++ component). |
| [Raspberry Pi (Zero 2 W or larger)](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) | ✅ datasheet (2026-10-11) | For heavier on-device biometrics (piezo grid). Confirmed: quad Cortex-A53 at 1 GHz, 512 MB RAM, 2.4 GHz Wi-Fi + BT 4.2, 40-pin header (unpopulated on the base model), in production until at least January 2030. |

## `temp_sensors` 🛡 · Control

**Requirement:** Read by the firmware today, per zone: one water temperature (G1/4 inline 10k NTC, ADS1115 ch0/ch2) and one TEC hot-face/heatsink temperature (10k NTC, ch1/ch3). Room temperature/RH (e.g. SHT45) on the hub for the dew-point guard. Planned, not yet read: water out, and a second sensor per cold plate for a plausibility check.

| Example | Status | Notes |
|---|---|---|
| [Alphacool Eiszapfen inline temperature sensor G1/4 (10k NTC)](https://download.alphacool.com/datasheet/ENG_17597_Alphacool_Eiszapfen_temperature_sensor_flat_G1-4_-_chrome_datasheet.pdf) | ✅ datasheet (2026-10-10) | B-value and tolerance not published, so calibrate each sensor (ice bath + 40 °C bath). Rated to 60 °C max. |
| [XSPC G1/4 inline 10k sensor](https://www.watercoolinguk.co.uk/product/xspc-g1-4-inline-10k-sensor-chrome/) | 🟡 listing (2026-10-10) |  |
| [Sensirion SHT45 (room temperature/RH, dew point)](https://sensirion.com/products/catalog/SHT45) | ✅ datasheet (2026-10-10) |  |

## `thermal_cutoff` 🛡 · Control

**Requirement:** Bimetal, normally closed, auto-reset: opens at 50 °C (cold plates) and 80 °C (heatsinks). Switches relay coils, not load current. Certified (UL/VDE/ENEC) preferred.

| Example | Status | Notes |
|---|---|---|
| [KSD301 / KSD9700 class, NC, 50 °C and 80 °C](https://www.ebay.de/itm/394903220088) | 🟡 listing (2026-10-11) | Cheap, but the listings show no certification, and retail listings often mix up NO and NC at 50 C. Datasheets found (KSD9700 spec sheets) show 250 V / 5 A (CQC) or 10 A resistive, +-5 C tolerance, reset >= 35 C for the 50 C NC part; UL is often only 125 V. Test every unit (hot-air gun + thermometer) before use. |
| [Sensata-Airpax 67L050 (NC, opens on rise at 50 C) and 67L080 (NC, 80 C)](https://www.digikey.cn/en/products/detail/sensata-airpax/67L050/1631970) | 🟡 listing (2026-10-11) | SPST NC bimetal, auto-reset, +-5 C. 67L050 resets at 30 C; 67L080 (https://nl.farnell.com/sensata-airpax/67l080/switch-thermal-n-c-80-c/dp/1524704) resets at 55 C. Rated only 0.5-1 A at 48 VDC / 120 VAC, which is plenty for a relay coil (the intended use) but not for load current. Per the Sensata 6700 datasheet VDE approval applies to the P (bracket) suffix; I found no UL listing, so the certification wish is only partly met. Manufacturer PDF not opened: only distributor excerpts, so treat as a listing. |
| [RS PRO bimetallic thermostats (UL/cUL/ENEC listed)](https://uk.rs-online.com/web/p/thermostatic-switches/2228228) | 🟡 listing (2026-10-10) | The certified part found has the wrong temperature (70 °C). Help wanted: a certified NC part at 50 °C. |

## `leak_sensor` 🛡 · Control

**Requirement:** Detects water in the hub drip tray and at the hub-side couplings; digital or analog input to the control MCU.

| Example | Status | Notes |
|---|---|---|
| [HW group WLD Relay + WLD sensing cable](https://hw-group.com/support/top-selling-wld-component-wld-relay) | 🟡 listing (2026-10-11) | 12 V module with a cable (rope) input that also alarms when the sensing cable is disconnected, so it is open-wire detectable. Output contact rating not stated on the page: check before wiring to a 3.3 V GPIO (use the contact with a pull-up, or an optocoupler). |
| [Andel Floodline Leak 1 Mk II (rope/cable leak panel)](https://a.storyblok.com/f/121333/x/ed8fe6cc90/42-floodline-leak-1-mkii.pdf) | 🟡 listing (2026-10-11) | 12 or 24 V AC/DC supply; SPCO relay output 1 A at 24 VDC for 'leak' and a system-fault output for sensor or lead cable damage or disconnection. Bulky, so mounting space in the hub matters. A bare conductive-polymer rope on a raw GPIO is NOT recommended: it reads only ~20-150 on a 10-bit ADC, and DC excitation corrodes it. |

## `tec_module` · Thermal

**Requirement:** 40×40 mm, 127 couples, Imax ≈ 6 A, Vmax ≈ 15 V. Datasheet with Qmax/ΔTmax curves preferred.

| Example | Status | Notes |
|---|---|---|
| [TEC1-12706 (HB / Thermonamic datasheet)](https://akizukidenshi.com/goodsaffix/TETC1-12706.pdf) | ✅ datasheet (2026-10-10) | Qmax 50 W, ΔTmax 66 K, Imax 6.4 A, Vmax 14.4 V, R 1.98 Ω. Quality varies a lot between sellers, so buy from a source with a datasheet. |
| [Same Sky CP85438](https://www.digikey.com/en/products/detail/same-sky-formerly-cui-devices/CP85438/1747374) | 🟡 listing (2026-10-10) | Branded, datasheet-backed, but an 8.5 A part: adjust max_tec_current_a and re-run the kit check. |

## `cold_plate` · Thermal

**Requirement:** Aluminium or copper water block for 40×40 mm TECs, G1/4 or barbed ports. Do not mix copper and aluminium in one loop.

| Example | Status | Notes |
|---|---|---|
| [Generic 40×40 / 40×80 mm aluminium water block](https://hackaday.io/project/205182-opencooler) | 🟡 listing (2026-10-10) | Thermal resistance is never published, so it goes on the prototype measurement list. |

## `heatsink` · Thermal

**Requirement:** Heat rejection ≤ 0.07 K/W per zone (Duo) or ≤ 0.11 K/W (Solo) at quiet fan speed (bedroom target ≤ 30 dB(A) at 1 m).

| Example | Status | Notes |
|---|---|---|
| [CPU tower cooler per TEC (TEC sandwiched between water block and cooler)](https://hackaday.io/project/205182-opencooler) | ❔ unverified (2026-10-10) | Measure the real K/W. A failed DIY build (opencooler V1) suggests undersized heat rejection is the most common failure. |
| [Single-TEC 'peltier water cooling kit' (block + 40 mm fan)](https://www.makerlab-electronics.com/products/thermoelectric-tec12706-tec-12706-peltier-cooling-system-heatsink-kit-air-cooled-liquid-cooled) | ❌ rejected (2026-10-10) | 40 mm fans are far too small and loud for this heat load. |

## `pump` 🛡 · Thermal

**Requirement:** 12 V, tach output, ≥ 0.5 L/min at ≥ 1 m head, continuous duty, quiet at low speed (PWM).

| Example | Status | Notes |
|---|---|---|
| [Laing/Xylem D5 PWM 12 V](https://www.watercoolinguk.co.uk/product/laing-flojetd5-pwm-pump-motor-12v-1200-lph/) | 🟡 listing (2026-10-10) | Massively oversized (max ~3.7 m head), but reliable, with tach and PWM. Run it slow for silence. |
| [Laing DDC 12 V PWM](https://www.aquatuning.com/en/watercooling/custom/pumps) | 🟡 listing (2026-10-10) |  |
| DC40-class brushless 12 V pump | ❔ unverified (2026-10-10) | Cheaper; sold under many names on marketplaces (search "DC40 12V brushless pump tach"). Check that it has a tach wire. |

## `flow_sensor` 🛡 · Thermal

**Requirement:** Reliable reading at 0.15–1 L/min (the flow interlock trips below 0.15 L/min).

| Example | Status | Notes |
|---|---|---|
| [Aqua Computer MPS Flow 100 (20–100 l/h)](https://www.watercoolinguk.co.uk/p/Aquacomputer-flow-sensor-MPS-Flow-100_69575.html) | 🟡 listing (2026-10-10) | Range matches our flow best. |
| [Gems FT-110 turbine](https://www.farnell.com/datasheets/1877507.pdf) | ✅ datasheet (2026-10-10) | ±3 % of reading, 0.5 L/min minimum, so it is borderline at our lowest flow. |
| [YF-S401 hall turbine](https://wiki.dfrobot.com/sen0216/) | 🟡 listing (2026-10-10) | Cheap. ±5 % at 0.3–3 L/min per DFRobot; calibrate it. |

## `reservoir` 🛡 · Thermal

**Requirement:** ≈ 0.5 L, top fill port, air purge, non-contact level sensor for the LOW_WATER fault.

| Example | Status | Notes |
|---|---|---|
| PC-watercooling tube reservoir + capacitive non-contact level sensor | ❔ unverified | Help wanted. |

## `quick_disconnect` 🛡 · Water mat

**Requirement:** Dry-break (non-spill) couplings at the hub for each line. Spill per disconnect ≤ 0.5 mL.

| Example | Status | Notes |
|---|---|---|
| [CPC NS4 non-spill coupling](https://avantorsciences.com/mx/en/product/39537527/cpc-non-spill-quick-disconnect-fittings-bodies-and-inserts) | 🟡 listing (2026-10-10) | < 0.1 mL spill per disconnect (CPC data via a distributor). Commercial bed-cooling systems also use CPC-type couplings. |
| [Alphacool Eiszapfen quick-release coupling G1/4](https://shop.alphacool.com/en/shop/fittings/quick-release-fasteners/ank-alphacool-eiszapfen-quick-release-coupling-set-g1/4-ag-chrome) | 🟡 listing (2026-10-10) | No spill figure published. One DIY builder reported quick disconnects that did not self-seal, so test before use. |

## `water_mat` 🛡 · Water mat

**Requirement:** Even water distribution under one sleeper's torso and legs, comfortable, does not kink under body weight, works at ≤ 0.5 bar, washable or covered.

The hardest part to source, and the most needed contribution. Parallel channels (not one long serpentine) keep flow resistance low and prevent pinch-off.

| Example | Status | Notes |
|---|---|---|
| [DIY: 4 mm ID reinforced tubing in channels cut into a 1.5" foam topper (~30 m per mat)](https://techteamgb.co.uk/2024/11/18/i-made-a-custom-bed-watercooler-open-source-diy-bed-cooler-heater-eight-sleep-type-thing/) | 🟡 listing (2026-10-10) | Documented DIY build. 8 mm tubing was too stiff. |
| [Replacement pads of commercial bed-cooling systems (optional, never a dependency)](https://sleepme.helpjuice.com/ooler-repair-kit-a) | ❔ unverified (2026-10-10) | Check the coupling type and pressure rating before connecting one. |
| Custom welded TPU channel mat | ❔ unverified | Target for Tier 1. Help wanted: textile/RF-welding experience. |

## `bcg_sensing` · Sensing

**Requirement:** Presence, plus heart rate and breathing via ballistocardiography (BCG). Three options; see docs/design/03-sensing-biometrics.md.

| Example | Status | Notes |
|---|---|---|
| [Load cells under the bed legs + HX711 (ESPHome)](https://community.home-assistant.io/t/bed-scale-occupancy-sensor/114205) | 🟡 listing (2026-10-10) | Presence is proven in many ESPHome builds. 80 SPS is enough for heart rate in principle (published BCG work uses 50–200 Hz), but this is unproven in Open Bed Climate. |
| [Pneumatic: air tube/bladder under the mattress + pressure sensor](https://doaj.org/article/aa0acc60ad3748178aa63cd2062f426e) | ❔ unverified (2026-10-10) | Commercial sleep analyzers use this principle. Untested with a water mat above it (one vendor warns about waterbeds). |
| [Piezo film grid (TE LDT0-028K) + TI ADS131M08 simultaneous-sampling ADC](https://www.ti.com/product/ADS131M08) | ✅ datasheet (2026-10-10) | Tier 1: there is no off-the-shelf ADS131M08 breakout (only TI's EVM), so it goes on the cover sensor board. |

## `vibration_motor` · Add-ons

**Requirement:** Silent vibration alarm under the pillow or cover.

| Example | Status | Notes |
|---|---|---|
| [Adafruit DRV2605L haptic driver (product 2305) + ERM/LRA puck](https://www.adafruit.com/products/2305) | 🟡 listing (2026-10-10) |  |

## `adjustable_base` · Add-ons

**Requirement:** Use an existing adjustable base with a community Home Assistant integration (elevation, anti-snore).

| Example | Status | Notes |
|---|---|---|
| [ha-adjustable-bed (HACS) — Linak, Keeson/Ergomotion, Richmat, Okin, Octo, Jiecang, Leggett & Platt, …](https://github.com/kristofferR/ha_smartbed) | 🟡 listing (2026-10-10) | Bluetooth; works through an ESPHome Bluetooth proxy, which the ESP32-S3 hub can be. |
