# Shopping list: solo-starter

<!-- GENERATED from shopping/solo-starter.toml by `python -m opod.shopping`. Edit the .toml, not this file. -->

> **Prices change. Checked on 2026-10-11** (Germany / EU, prices incl. VAT, EUR). Shipping not included.
> 🟡 listing = price seen on the shop page · ❔ estimate = not confirmed, reasoned guess (48 lines).
> Read [SAFETY.md](../../SAFETY.md) and [WIRING.md](../WIRING.md) before ordering. Role ids link to [PARTS.md](../PARTS.md).

| | EUR |
|---|---:|
| Subtotal stage 1 (bench) | 1,083.90 |
| Subtotal stage 2 (bed) | 261.86 |
| **Total (bench + bed)** | **1,345.76** |
| Lines marked estimate | 48 |

Tools are listed with qty 0 and are not in the totals.

## Notes

Shipping is not included (expect ~6 EUR per shop; ~8 shops). Prices change; re-check before ordering.
Loop size is 13/10 mm (ID 10 / OD 13) everywhere except the cold-plate barbs and the mat's 4 mm channels.
Metals: brass/copper only (G1/4 fittings, QD3, sensors, copper cold plates). No aluminium in the wet path (parts.toml).
Pump + 6 fans must stay inside the kit's 25 W per-zone overhead budget: run the DDC at <= 50 % and the fans at quiet speed.
Sensors match the firmware (board.rs): one ADS1115 @ 0x48, zone 0 uses ch0 = water (inline NTC) and ch1 = TEC hot face
(bead NTC). Future, not bought: parts.toml also asks for water in AND out, dual NTCs per cold plate and an NTC on every
heatsink; add them when board.rs reads more channels.

## Stage 1: bench build (no bed, 10 l water container as thermal load)

### Power

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`tec_psu`](../PARTS.md) | Mean Well GST280A24-C6P (24 V / 11.67 A, IEC C14, desktop) | 1 | 94.80 | 94.80 | [Reichelt](https://www.reichelt.de/de/de/shop/produkt/tischnetzteil_280_w_24_v_11_67_a-171084) | 🟡 listing | Reichelt no. MW GST280A24. Output is a 6-pin Molex plug: see the mating-connector line. |
| [`aux_psu`](../PARTS.md) | Mean Well GST90A12-P1M (12 V / 6.67 A, IEC C14, desktop) | 1 | 30.40 | 30.40 | [Reichelt](https://www.reichelt.com/de/en/shop/product/desktop_power_supply_80_w_12_v_6_67_a-171058) | 🟡 listing | Reichelt no. MW GST90A12. 5.5 x 2.5 mm barrel plug, center positive. |
| [`tec_drive`](../PARTS.md) | RD DPS5020 programmable buck module, communication version (USB-BT) | 1 | 75.00 | 75.00 | [Amazon.de](https://www.amazon.de/s?k=DPS5020) | ❔ estimate | Amazon.de only (no German electronics distributor carries it). US listings ~USD 64-107. Buy the communication version: it exposes the TTL UART used for Modbus. Measure output ripple (parts.toml asks). |
| [`polarity_relay`](../PARTS.md) | Automotive relay 12 V coil, 30/40 A, 1 changeover (SPDT, ISO mini, 5-pin) | 3 | 5.49 | 16.47 | [Conrad](https://www.conrad.de/de/f/kfz-relais-12v-1725369.html) | ❔ estimate | 1x zone enable relay (coil through the cutoff chain, load on NO) + 2x SPDT wired H-bridge style for polarity (parts.toml allows this instead of one 20 A DPDT). TECs see <= 14 V, inside the 14 V automotive rating. Price from the category page, exact part not pinned. |
| [`polarity_relay`](../PARTS.md) | Relay socket for ISO mini relay with pigtail leads (>= 2.5 mm2 load leads) | 3 | 3.00 | 9.00 | [Conrad](https://www.conrad.de/de/f/kfz-relais-12v-1725369.html) | ❔ estimate |  |
| [`polarity_relay`](../PARTS.md) | Inline ATO/ATC blade fuse holder, waterproof, 2.5-4 mm2 leads | 1 | 4.00 | 4.00 | [Conrad](https://www.conrad.de/de/search.html?search=flachsicherungshalter%20fliegend) | ❔ estimate | Per-zone DC fuse in the TEC path (parts.toml role polarity_relay). |
| [`polarity_relay`](../PARTS.md) | ATO blade fuse 20 A (pack of 10) | 1 × 10 | 3.50 | 3.50 | [Conrad](https://www.conrad.de/de/search.html?search=flachsicherung%2020A) | ❔ estimate |  |

### Consumables

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| consumable | IEC C13 mains cord with Schuko plug, 1.8 m | 2 | 4.80 | 9.60 | [Reichelt](https://www.reichelt.de/de/de/shop/search/kaltger%C3%A4tekabel%201,8m) | ❔ estimate | Both GST supplies ship without a mains cord. Price from the search page, exact item not pinned. |
| consumable | Molex Mini-Fit Jr 6-pin receptacle + crimp terminals (mates the GST280 C6P plug) | 1 | 4.00 | 4.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/mini-fit%20jr%206) | ❔ estimate | Or cut the DC plug off (DC side only, never the mains side) and put ferrules on the 16 AWG leads. Check the pinout in the GST280A datasheet. |
| consumable | DC barrel jack 5.5 x 2.5 mm to screw terminal adapter | 1 | 1.50 | 1.50 | [Berrybase](https://www.berrybase.de/en/search?search=hohlstecker%20schraubklemme) | ❔ estimate | For the GST90A12 12 V output. |
| consumable | Elecrow UART TTL to RS485 converter, half duplex, 3.3-5 V (Modbus to the DPS) | 2 | 1.90 | 3.80 | [Berrybase](https://www.berrybase.de/en/search?search=CIA00485T) | ❔ estimate | One at the DPS UART, one at the Pico (WIRING.md: one RS-485 bus). Stand-in for a MAX3485 module; if the module switches direction itself, GP6 (DE) stays unused. Price (1.90 EUR) seen in a related-items block, not on its own product page. |
| consumable | DC-DC buck converter 12 V to 5 V, >= 3 A (powers Pico 2, ESP32-S3, sensors) | 1 | 6.00 | 6.00 | [Berrybase](https://www.berrybase.de/en/search?search=step%20down%205V%203A) | ❔ estimate | Fed from the 12 V aux supply. Pico 2 via VSYS, ESP32-S3 via its 5 V pin; common GND at the star point. |
| consumable | 4-channel logic-level MOSFET switch module (3.3 V input, >= 5 A per channel) | 1 | 7.00 | 7.00 | [Amazon.de](https://www.amazon.de/s?k=4+kanal+mosfet+modul+3.3V) | ❔ estimate | Low-side drivers: GP10 zone relay coil, GP11 both polarity coils, GP12 pump, GP13 fans. Add the external 10 k pull-downs (WIRING.md); do not rely on the module's own. |
| consumable | 1N5408 rectifier diode (flyback across each relay coil, pack of 10) | 1 × 10 | 1.50 | 1.50 | [Reichelt](https://www.reichelt.de/de/de/shop/search/1n5408) | ❔ estimate | 1N4007 works as well for 12 V relay coils. Skip if the relays you buy have a built-in diode (then mind the coil polarity). |
| consumable | Pin header set for Raspberry Pi Pico | 1 | 0.50 | 0.50 | [Berrybase](https://www.berrybase.de/en/search?search=RPIP-PINH) | ❔ estimate | BerryBase RPIP-PINH, 0.50 EUR seen on berrybase.at. |
| consumable | Resistor 10 kOhm 1/4 W (pull-ups / pull-downs, pack of 100) | 1 × 100 | 1.50 | 1.50 | [Reichelt](https://www.reichelt.de/de/de/shop/search/metallschicht%2010k) | ❔ estimate |  |
| consumable | Resistor 4.7 kOhm 1/4 W (MOSFET gate pull-downs, DS18B20 pull-up; pack of 100) | 1 × 100 | 1.50 | 1.50 | [Reichelt](https://www.reichelt.de/de/de/shop/search/metallschicht%204,7k) | ❔ estimate | RP2350 erratum E9: external pull-downs should be <= 8.2 k, so use 4.7 k on the driver inputs (WIRING.md still says 10 k: open item). |
| consumable | 1N5819 Schottky diode (Pico VSYS / ESP32 5 V OR-ing, pack of 10) | 1 × 10 | 1.00 | 1.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/1n5819) | ❔ estimate | Lets USB and the 5 V buck feed the boards without back-feeding each other. |
| consumable | Resistor 120 Ohm (RS-485 termination) + 2.2 k / 3.3 k (spare dividers for 5-12 V signals) | 1 | 1.00 | 1.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/metallschicht%20120) | ❔ estimate |  |
| consumable | Perfboard 160 x 100 mm + 2-pin/3-pin PCB screw terminals (5.08 mm, ~20 pcs) | 1 | 9.00 | 9.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/lochrasterplatine) | ❔ estimate |  |
| consumable | Raspberry Pi Debug Probe (optional, for defmt logs and flashing) | 1 | 12.20 | 12.20 | [Berrybase](https://www.berrybase.de/en/raspberry-pi-debug-probe) | 🟡 listing | Optional; a second Pico 2 with debugprobe firmware works too. WIRING.md bring-up step 1 uses it. |
| consumable | Single-core flexible wire H07V-K 2.5 mm2, red, per m (TEC path) | 5 | 0.80 | 4.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/h07v-k%202,5) | ❔ estimate | TEC path carries up to 15 A: >= 2.5 mm2 from DPS through fuse, relays to the TECs. |
| consumable | Single-core flexible wire H07V-K 2.5 mm2, black, per m (TEC path) | 5 | 0.80 | 4.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/h07v-k%202,5) | ❔ estimate |  |
| consumable | Stranded hook-up wire 0.25-0.5 mm2, assorted colours (signals, coils, sensors) | 1 | 12.00 | 12.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/litze%200,25) | ❔ estimate |  |
| consumable | WAGO 221-415 lever connector, 5-conductor, up to 4 mm2 | 10 | 0.95 | 9.50 | [Reichelt](https://www.reichelt.de/de/de/shop/produkt/verbindungsklemme_5-leiteranschluss-149800) | ❔ estimate | Price not shown in the fetched page. Use for the 24 V / 12 V / GND star point. |
| consumable | Knipex ferrule assortment, insulated, 0.5-2.5 mm2 (400 pcs) | 1 | 14.10 | 14.10 | [Reichelt](https://www.reichelt.de/de/de/shop/produkt/aderendhuelsen-sortiment_isoliert_0_5_-_2_5_mm_-222111) | 🟡 listing |  |
| consumable | Dupont jumper wires F-F / M-F (40 each) and heat-shrink assortment | 1 | 8.00 | 8.00 | [Berrybase](https://www.berrybase.de/en/search?search=jumper%20kabel) | ❔ estimate |  |
| consumable | TEC sandwich mounting: M3/M4 threaded rod, nuts, springs, 3 mm aluminium backplate | 3 | 5.00 | 15.00 | [Amazon.de](https://www.amazon.de/s?k=gewindestange+m4+edelstahl+federn+set) | ❔ estimate | Even clamping pressure on the ceramic; insulating washers so the block and cooler are not shorted through the screws. |
| consumable | Arctic MX-6 thermal paste, 4 g | 1 | 6.90 | 6.90 | [Caseking](https://www.caseking.de/en/search?search=arctic%20mx-6) | ❔ estimate | 6 TEC faces + NTC beads. |
| consumable | Barbed hose reducer 10 mm to 6 mm, straight (13/10 loop to the YF-S401) + 20 cm 6 mm ID tube + clamps | 2 | 2.50 | 5.00 | [Amazon.de](https://www.amazon.de/s?k=schlauchverbinder+reduzierst%C3%BCck+10mm+6mm) | ❔ estimate | Keep 5 cm of straight tube before the sensor. Plastic (PP/POM) reducers, no aluminium. |
| consumable | Alphacool Eiszapfen 13/10 mm compression fitting G1/4, deep black, six-pack | 2 × 6 | 35.62 | 71.24 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/fittings/compression-fittings/alphacool-eiszapfen-13/10mm-compression-fitting-g1/4-deep-black-sixpack) | 🟡 listing | Reservoir, pump outlet, flow sensor, T-adapter (2), cold-plate reducers; spares for the bed stage. Brass. |
| consumable | G1/4 T-adapter (3x inner thread), for the inline water temperature sensor | 1 | 5.00 | 5.00 | [Alphacool](https://shop.alphacool.com/en/shop/fittings) | ❔ estimate |  |
| consumable | Phobya EPDM tube 13/10 mm, black, per m | 8 | 4.49 | 35.92 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/fittings/compression-fittings/alphacool-eiszapfen-13/10mm-compression-fitting-g1/4-deep-black-sixpack) | 🟡 listing | Price shown as recommended accessory on the fittings page. 3 m loop + 5 m coiled in the 10 L bench container as the heat exchanger. Check per-m vs per-pack unit at checkout. |
| consumable | Reducers / short 10/8 mm tube and hose clamps to the cold-plate barbs | 1 | 10.00 | 10.00 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/fittings/quick-release-fittings) | ❔ estimate | Cold plates in series; match the barb OD of the blocks you receive. |
| consumable | Aqua Computer Double Protect Ultra, 5 l canister (ready-mixed coolant with inhibitor) | 1 | 32.90 | 32.90 | [Aqua Computer](https://shop.aquacomputer.de/Water-Cooling/Coolant/Double-Protect-Ultra-5l-canister::3127.html?language=en) | 🟡 listing | Distilled water + inhibitor in one. Enough for the loop plus the mat; replace yearly. |
| consumable | Distilled water 5 l (flushing and leak test) | 1 | 3.00 | 3.00 | [Amazon.de](https://www.amazon.de/s?k=destilliertes+wasser+5l) | ❔ estimate | Any drugstore. The bench container (10 l) can be plain tap water: the coil keeps it out of the loop. |
| consumable | Self-adhesive closed-cell insulation tape (Armaflex type), 3 mm x 50 mm x 15 m | 1 | 12.00 | 12.00 | [Aquatuning](https://www.aquatuning.com/en/aquaristics) | ❔ estimate | Wrap cold plates and short lines against condensation (02-electrical-safety.md). |
| consumable | Electronics enclosure, ABS ~250 x 200 x 100 mm (dry compartment, above water level) | 1 | 25.00 | 25.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/kunststoffgeh%C3%A4use%20abs) | ❔ estimate |  |
| consumable | Drip tray: plastic storage tray ~60 x 40 cm, low rim (holds the wet parts and the leak cable) | 1 | 10.00 | 10.00 | [Amazon.de](https://www.amazon.de/s?k=auffangwanne+kunststoff+60x40) | ❔ estimate |  |

### Control

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`control_mcu`](../PARTS.md) | Raspberry Pi Pico 2 (RP2350), SC1631 | 1 | 4.90 | 4.90 | [Reichelt](https://www.reichelt.com/de/en/shop/product/raspberry_pi_pico_2_rp235x_cortex-m33_microusb-383358) | 🟡 listing | Without headers; see the pin-header line. |
| [`temp_sensors`](../PARTS.md) | ADS1115 4-channel 16-bit ADC breakout | 1 | 5.60 | 5.60 | [Berrybase](https://www.berrybase.de/en/search?search=ADS1115) | 🟡 listing | Address 0x48 (ADDR to GND). ch0 water, ch1 hot face; ch2/ch3 belong to zone 1 (Duo kits). |
| [`temp_sensors`](../PARTS.md) | Alphacool Eiszapfen temperature sensor flat G1/4, 10k NTC (water, return line) | 1 | 10.98 | 10.98 | [Alphacool](https://shop.alphacool.com/en/shop/controllers-and-sensors/temperature-sensor/sen-alphacool-eiszapfen-temperature-sensor-flat-g1/4-black) | 🟡 listing | ADS ch0. Screws into a free G1/4 port (the T-adapter in the return line, WIRING.md). A second one for water-in is future. B value not published: calibrate in an ice bath and at ~40 C. |
| [`temp_sensors`](../PARTS.md) | 10k NTC epoxy bead thermistor, B ~3950, with leads (TEC hot face, + 2 spares) | 3 | 1.20 | 3.60 | [Reichelt](https://www.reichelt.de/de/de/shop/search/ntc%2010k) | ❔ estimate | ADS ch1: one on the heatsink base of the middle TEC, clamped with thermal paste. Two spares for calibration losses. Calibrate like the inline sensor. |
| [`temp_sensors`](../PARTS.md) | Adafruit SHT45 breakout (room temperature / humidity for the dew-point guard) | 1 | 13.00 | 13.00 | [Berrybase](https://www.berrybase.de/en/search?search=SHT45) | ❔ estimate | Read by the ESP32-S3 hub (02-electrical-safety.md, Condensation). |
| [`temp_sensors`](../PARTS.md) | Metal film resistor 10 kOhm 0.1 % (NTC divider references) | 4 | 0.40 | 1.60 | [Reichelt](https://www.reichelt.de/de/de/shop/search/10k%200,1%25) | ❔ estimate | 2 used (ch0, ch1) + 2 spares. Not the same as the generic 10 k pull resistors. |
| [`thermal_cutoff`](../PARTS.md) | Bimetal thermostat, normally closed (Oeffner), 50 C, auto-reset (cold plates) | 3 | 2.98 | 8.94 | [sensorshop24](https://www.sensorshop24.de/bimetall-temperaturschalter-thermostat-oeffner-schliesser) | 🟡 listing | Select Oeffner + 50 C. Uncertified. Test every unit with a hot-air gun and a thermometer; consider one spare. |
| [`thermal_cutoff`](../PARTS.md) | Bimetal thermostat, normally closed (Oeffner), 80 C, auto-reset (heatsink bases) | 3 | 2.98 | 8.94 | [sensorshop24](https://www.sensorshop24.de/bimetall-temperaturschalter-thermostat-oeffner-schliesser) | 🟡 listing | Select Oeffner + 80 C. All six in series in the zone-relay coil circuit (12 V, coil current only). |
| [`leak_sensor`](../PARTS.md) | HW group Sensor WLD Relay 1W-UNI (incl. 2 m WLD sensing cable A) | 1 | 95.00 | 95.00 | [BellEquip (AT)](https://www.bellequip.at/produkte/sensoren-wasser-und-leckage/sensor-wld-relay-1w-uni-hw-group-wassleck-detektor-mit-relais-ausgang) | ❔ estimate | Relay output signals water OR disconnected cable (fault output). Price not shown on the page. Wire the contact so dry = LOW at GP21 with the 10 k pull-up (WIRING.md). Kept after a second search (2026-10-11): the cheap relay-output leak modules (ATO, Amazon 12 V modules, Winland WaterBug) only alarm on water and do not report an open or unplugged sensor cable, so a broken wire would read as dry. The WLD relay also switches on cable disconnect, which matches the firmware input (HIGH = leak or open wire). Cheaper fail-safe fallback: an NC float switch in the drip tray wired to GND (dry = LOW, float lifts or wire breaks = HIGH), but it only reacts to ~1 cm of standing water, not to drops. |

### Hub

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`hub_controller`](../PARTS.md) | Espressif ESP32-S3-DevKitC-1-N8R8 | 1 | 18.90 | 18.90 | [Berrybase](https://www.berrybase.de/en/espressif-esp32-s3-devkitc-1-development-kit-esp32-s3-wroom-wifi-bluetooth-le-240mhz-5v-3-3v-01a0a08fef6771fab6d4b97a830c7c92) | ❔ estimate | 18.90 EUR (BerryBase ADA5336) seen in a related-items block; check the SKU is N8R8. Mouser EU lists it at ~11-13 EUR net. |

### Thermal

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`tec_module`](../PARTS.md) | Peltier module 40 x 40 x 3.8 mm, 6.0 A, 15.4 V, 51.4 W (Reichelt TECB 1) | 3 | 28.40 | 85.20 | [Reichelt](https://www.reichelt.de/de/de/shop/produkt/thermo-modul_peltierelement_40x40x3_8mm-32052) | 🟡 listing | Sold singly, in stock. Specs close to the TEC1-12706 the model uses; get the datasheet from the product page and compare Qmax/R. TEC1 127 05 (23.95 EUR) is the limited-stock alternative. |
| [`cold_plate`](../PARTS.md) | Copper water block 40 x 40 mm for Peltier modules, barbed ports | 3 | 10.00 | 30.00 | [Amazon.de](https://www.amazon.de/s?k=kupfer+wasserk%C3%BChlblock+40x40) | ❔ estimate | Copper, not aluminium (no mixed metals). Barbs are ~8 mm OD: see the reducer line. Lap flat if needed. |
| [`heatsink`](../PARTS.md) | Arctic Freezer 36 CO tower cooler (2x 120 mm PWM, continuous-operation fans) | 3 | 22.90 | 68.70 | [Caseking](https://www.caseking.de/en/aircooling/coolers/cpu-coolers) | 🟡 listing | One per TEC (hot side). CO fans are rated for 24/7. Measure the real K/W (kit assumes 0.11 K/W per zone). Socket mounts do not fit a TEC: see the mounting line. |
| [`pump`](../PARTS.md) | Alphacool Laing DDC310 Single Edition, silver (12 V, tach) | 1 | 68.58 | 68.58 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/pumps/laing-ddc/ddc-pumps/alphacool-laing-ddc310-single-edition-silver) | 🟡 listing | Pump without top: mounts into the Eisstation DDC reservoir below. Low-noise DDC; verify head (>= 1 m), tach wire and PWM on the product page. Tach to a Pico input via the 10 k pull-up. |
| [`reservoir`](../PARTS.md) | Alphacool Eisstation DDC - Solo reservoir (mounts directly on the DDC pump, G1/4) | 1 | 34.63 | 34.63 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/reservoirs/reservoir-without-pump/for-ddc/alphacool-eisstation-ddc-solo-reservoir) | 🟡 listing | Cheapest reservoir found in a German shop that takes the bare DDC310 (so no separate pump top). Smaller than the ~0.5 L target in parts.toml: fine for prototype 0 (the bench loop has the 10 l container on a coil, the bed loop adds the mat volume); verify volume and fill port on arrival. Plastic (non-metallic) wall, so the capacitive level sensor works if the wall is <= 20 mm. Upgrade path: Watercool HEATKILLER Tube 200 DDC (~500 ml glass, ~115 EUR). |
| [`reservoir`](../PARTS.md) | XKC-Y25-NPN non-contact capacitive level sensor, 5-12 V (LOW_WATER) | 1 | 8.00 | 8.00 | [Amazon.de](https://www.amazon.de/s?k=XKC-Y25-NPN) | ❔ estimate | Taped to the reservoir wall at the minimum level (non-metallic wall <= 20 mm). Listings give 'output high level = VCC', so it may drive its supply voltage: power it at 5 V (not 12 V), put a divider (e.g. 2.2 k / 3.3 k) into GP22, and measure the idle output before connecting. Wanted: LOW = water present (level OK), HIGH = low water or broken wire (WIRING.md). Verify the polarity of your unit; add an inverter if it is reversed. |
| [`flow_sensor`](../PARTS.md) | YF-S401 hall flow sensor, 98 Hz per L/min, 7 mm barbs (for 6 mm ID hose) | 1 | 4.00 | 4.00 | [TinyTronics (NL, ships to DE)](https://www.tinytronics.nl/en/sensors/liquid/yf-s401-water-flow-sensor) | 🟡 listing | Matches the prebuilt Solo UF2: FLOW_HZ_PER_LPM = 98 (Q [L/min] = f [Hz] / 98, per the listing). Range 0.3-6 L/min, +-10 %: our 0.4-0.6 L/min is at the low end, so calibrate with a measuring jug and a stopwatch. Below 0.3 L/min it reads low or zero, so the 0.15 L/min interlock trips early (safe side). Output is open-collector style: power at 5 V, signal to GP14 with the 3.3 V pull-up (measure the idle level first; use a divider if it shows 5 V). Flow direction arrow matters. Upgrade: Aqua Computer mps flow 100 (G1/4, 20-100 l/h, no moving parts, ~55 EUR): its alarm output can be set to an rpm signal via USB, but the exact pulses per litre are not documented for it (the high flow NEXT manual gives 100 l/h = 1000 rpm), so it needs a measured factor and a source build with a new FLOW_HZ_PER_LPM. |

### Bench rig

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| bench | Insulated cool box ~10 l (thermal load: the 'sleeper' for bench tests) | 1 | 25.00 | 25.00 | [Amazon.de](https://www.amazon.de/s?k=k%C3%BChlbox+10l+passiv) | ❔ estimate | Filled with water; the 5 m tube coil lies in it. Lid with two holes for the lines. |
| bench | DS18B20 waterproof temperature probe, 1 m cable (bath temperature, logged by the hub) | 1 | 3.50 | 3.50 | [Berrybase](https://www.berrybase.de/en/search?search=DS18B20%20wasserdicht) | ❔ estimate | On the ESP32-S3 (ESPHome dallas) with a 4.7 k pull-up. With the coil, the firmware NTC sees only loop water; this logs the 10 l bath in Home Assistant. |
| bench | Power resistor 1 Ohm, >= 100 W, aluminium housing (DPS bring-up dummy load) | 1 | 8.00 | 8.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/hochlastwiderstand%201%20ohm) | ❔ estimate | WIRING.md bring-up step 3: test the DPS on a 1 Ohm load before any TEC, set to 1-2 A from the DPS front panel (not from the Pico, which would request up to 15 A = 225 W into 1 Ohm). Mount on a heatsink. |

**Subtotal bench: 1,083.90 EUR**

## Stage 2: bed (add to the bench build)

### Water mat

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`quick_disconnect`](../PARTS.md) | Koolance QD3 no-spill female, straight, 13/10 mm, black | 2 | 22.98 | 45.96 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-water-cooling/fittings/quick-release-fittings/koolance-qd3-quick-disconnect-no-spill-female-straight-for-13/10mm-3/8-x-1/2-tubing-black) | 🟡 listing | ~0.2 ml freed per disconnect (Koolance spec), inside the 0.5 ml target. Hub side. |
| [`quick_disconnect`](../PARTS.md) | Koolance QD3 no-spill male, straight, 13/10 mm, black | 2 | 21.98 | 43.96 | [Aquatuning](https://www.aquatuning.com/en/koolance) | ❔ estimate | The 16/10 male is listed at 21.98 EUR; 13/10 assumed the same. Mat side. |
| [`water_mat`](../PARTS.md) | DIY mat: PVC tube 4 mm ID / 6 mm OD (fabric-reinforced if available), per m | 30 | 1.20 | 36.00 | [Amazon.de](https://www.amazon.de/s?k=pvc+schlauch+4mm+innen+6mm+au%C3%9Fen) | ❔ estimate | Documented DIY build (parts.toml water_mat): ~30 m in parallel channels, not one serpentine. 8 mm was too stiff in that build. A generic water-perfused cooling pad bought in the EU is an acceptable v0 stopgap (never a commercial bed system's pad as a dependency). |
| [`water_mat`](../PARTS.md) | DIY mat: foam topper 90 x 200 cm, ~4 cm (channels cut in) | 1 | 45.00 | 45.00 | [Amazon.de](https://www.amazon.de/s?k=schaumstoff+topper+90x200+4cm) | ❔ estimate |  |
| [`water_mat`](../PARTS.md) | DIY mat: 1-to-8 manifold, 10 mm inlet to 8x 4 mm barbs (supply + return) | 2 | 12.00 | 24.00 | [Amazon.de](https://www.amazon.de/s?k=verteiler+messing+4mm+schlauch+8+fach) | ❔ estimate | Must be pressure-rated (brass or PP), not an aquarium air manifold. Parallel channels keep flow resistance low. |

### Consumables

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| consumable | Phobya EPDM tube 13/10 mm, black, per m (insulated bed lines, 2 x 3 m) | 6 | 4.49 | 26.94 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/fittings/compression-fittings/alphacool-eiszapfen-13/10mm-compression-fitting-g1/4-deep-black-sixpack) | 🟡 listing |  |
| consumable | Closed-cell tube insulation for 13 mm OD tube, 2 m pieces | 3 | 5.00 | 15.00 | [Amazon.de](https://www.amazon.de/s?k=armaflex+schlauch+13mm) | ❔ estimate | Against condensation and heat loss on the hub-to-mat lines. |

### Control

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`leak_sensor`](../PARTS.md) | HW group WLD sensing cable A, extra length for the hub-side couplings | 1 | 25.00 | 25.00 | [BellEquip (AT)](https://www.bellequip.at/produkte/sensoren-wasser-und-leckage/sensor-wld-relay-1w-uni-hw-group-wassleck-detektor-mit-relais-ausgang) | ❔ estimate | Optional: route under the QD3 couplings; the included 2 m covers the drip tray. |

**Subtotal bed: 261.86 EUR**

## Tools (not in the totals; qty 0 = you probably own it)

### Tools

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| tool | Digital multimeter (CAT III) | 0 | 30.00 | 0.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/multimeter) | ❔ estimate |  |
| tool | DC clamp meter (Hall, >= 20 A DC) for TEC current checks | 0 | 45.00 | 0.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/stromzange%20dc) | ❔ estimate | AC-only clamp meters do not read the TEC current. |
| tool | Ferrule crimping tool (0.25-6 mm2) | 0 | 25.00 | 0.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/crimpzange%20aderendh%C3%BClsen) | ❔ estimate |  |
| tool | Soldering iron + solder | 0 | 40.00 | 0.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/l%C3%B6tstation) | ❔ estimate |  |
| tool | Hot-air gun (bimetal cutoff test) | 0 | 25.00 | 0.00 | [Amazon.de](https://www.amazon.de/s?k=hei%C3%9Fluftf%C3%B6hn) | ❔ estimate |  |
| tool | Reference thermometer with probe, 0.1 C resolution (NTC calibration) | 0 | 15.00 | 0.00 | [Amazon.de](https://www.amazon.de/s?k=einstichthermometer+0.1) | ❔ estimate |  |
| tool | Plug-in mains power meter (energy monitor socket) | 0 | 15.00 | 0.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/energiekostenmessger%C3%A4t) | ❔ estimate | Measures real wall power of both supplies during bench tests. |
| tool | Wire stripper and side cutter | 0 | 20.00 | 0.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/abisolierzange) | ❔ estimate |  |
