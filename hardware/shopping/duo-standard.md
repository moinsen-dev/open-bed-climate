# Shopping list: duo-standard

<!-- GENERATED from shopping/duo-standard.toml by `python -m obc.shopping`. Edit the .toml, not this file. -->

> **Prices change. Checked on 2026-10-12** (Germany / EU, prices incl. VAT, EUR). Shipping not included.
> 🟡 listing = price seen on the shop page · ❔ estimate = not confirmed, reasoned guess (49 lines).
> Read [SAFETY.md](../../SAFETY.md) and [WIRING.md](../WIRING.md) before ordering. Role ids link to [PARTS.md](../PARTS.md).

| | EUR |
|---|---:|
| Subtotal stage 1 (bench) | 2,225.87 |
| Subtotal stage 2 (bed) | 498.72 |
| **Total (bench + bed)** | **2,724.59** |
| Lines marked estimate | 49 |

Tools are listed with qty 0 and are not in the totals.

## Notes

Shipping is not included (expect ~6 EUR per shop; ~8 shops). Prices change; re-check before ordering.
Two zones = two separate water loops: per zone 4 TECs, 4 cold plates, 4 coolers, 1 DDC pump, 1 reservoir, 1 flow sensor, 1 DPS5020 and its own 24 V supply.
Loop size is 13/10 mm (ID 10 / OD 13) everywhere except the cold-plate barbs and the mat's 4 mm channels. Brass/copper only in the wet path.
Sensors match the firmware (board.rs, feature kit-duo-standard): one ADS1115 @ 0x48 with ch0/ch1 = zone 0 water/hot face and ch2/ch3 = zone 1;
pumps GP12/GP18, fans GP13/GP19, flow GP14/GP20; DPS Modbus addresses 1 and 2 on one RS-485 bus; one leak input (GP21) and one level input (GP22).
Level: each loop has its own reservoir, but board.rs reads one level input, so the two sensors are OR-ed into GP22 (either low = LOW_WATER for both zones). Open item: a second level input in board.rs, or a shared two-chamber reservoir.
Aux supply: the GST120A12 is 102 W at 12 V (duo-standard.toml: aux_psu_w = 102). The kit check passes: 65 W is 64 % of 102 W.
12 V load as listed: at full speed, per zone 8 fans x 2.4 W + one DDC (~10 W) + 3 relay coils (~1.8 W each) = ~35 W, plus ~5 W electronics = ~74 W for two zones. That is over the model's 25 W per zone overhead, but inside 80 % of the 102 W aux supply (~6.2 A, inside the carrier's 7.5 A fuse). Since firmware 0.2 the Pico drives pumps and fans with 25 kHz PWM on their switched supply (fan duty follows hot-face temperature and TEC power, minimum 25 %), so the typical load and noise are lower; whether 16 fans meet the 30 dB(A) target is still to be measured.
Fuse: WIRING.md asks for 20 A per zone. At 4 x 4.5 A = 18 A continuous a 20 A blade fuse runs at 90 % of its rating; if it opens when warm, that is the reason (open item, not a reason to fit a bigger fuse without checking the wire).
Not bought: biometrics (bcg_sensing, pneumatic for this kit) are optional for prototype 0 and nothing in the firmware reads them yet.

## Stage 1: bench build (no bed, 10 l water container as thermal load)

### Power

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`tec_psu`](../PARTS.md) | Mean Well GST280A24-C6P (24 V / 11.67 A, IEC C14, desktop) | 2 | 94.80 | 189.60 | [Reichelt](https://www.reichelt.de/de/de/shop/produkt/tischnetzteil_280_w_24_v_11_67_a-171084) | 🟡 listing | Reichelt no. MW GST280A24. One per zone. Output is a 6-pin Molex plug: see the mating-connector line. |
| [`aux_psu`](../PARTS.md) | Mean Well GST120A12-R7B (12 V / 8.5 A = 102 W, IEC C14, desktop) | 1 | 47.40 | 47.40 | [Reichelt](https://www.reichelt.de/de/de/shop/produkt/tischnetzteil_100_w_12_v_8_5_a-171063) | 🟡 listing | Reichelt no. MW GST120A12. Rated 102 W at 12 V (Mean Well manual: 120 W only for the 20-48 V models), not 120 W. Two-zone aux load is 65 W = 64 % of 102 W, inside the 80 % margin. Output is a locking 4-pin DIN plug (R7B): see the DIN jack line. |
| [`tec_drive`](../PARTS.md) | RD DPS5020 programmable buck module, communication version (USB-BT) | 2 | 75.00 | 150.00 | [Amazon.de](https://www.amazon.de/s?k=DPS5020) | ❔ estimate | One per zone, Modbus addresses 1 (zone 0) and 2 (zone 1). 18 A per zone is inside its 20 A. Amazon.de only; buy the communication version (TTL UART for Modbus). Measure output ripple (parts.toml asks). |
| [`polarity_relay`](../PARTS.md) | Automotive relay 12 V coil, 30/40 A, 1 changeover (SPDT, ISO mini, 5-pin) | 6 | 5.49 | 32.94 | [Conrad](https://www.conrad.de/de/f/kfz-relais-12v-1725369.html) | ❔ estimate | Per zone: 1 zone enable relay (coil through that zone's cutoff chain, load on NO) + 2 SPDT wired H-bridge style for polarity. TECs see <= 14 V, inside the 14 V automotive rating. Price from the category page, exact part not pinned. |
| [`polarity_relay`](../PARTS.md) | Relay socket for ISO mini relay with pigtail leads (>= 2.5 mm2 load leads) | 6 | 3.00 | 18.00 | [Conrad](https://www.conrad.de/de/f/kfz-relais-12v-1725369.html) | ❔ estimate |  |
| [`polarity_relay`](../PARTS.md) | Inline ATO/ATC blade fuse holder, waterproof, 2.5-4 mm2 leads | 2 | 4.00 | 8.00 | [Conrad](https://www.conrad.de/de/search.html?search=flachsicherungshalter%20fliegend) | ❔ estimate | One DC fuse per zone in the TEC path (parts.toml role polarity_relay). |
| [`polarity_relay`](../PARTS.md) | ATO blade fuse 20 A (pack of 10) | 1 × 10 | 3.50 | 3.50 | [Conrad](https://www.conrad.de/de/search.html?search=flachsicherung%2020A) | ❔ estimate |  |

### Consumables

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| consumable | IEC C13 mains cord with Schuko plug, 1.8 m | 3 | 4.80 | 14.40 | [Reichelt](https://www.reichelt.de/de/de/shop/search/kaltger%C3%A4tekabel%201,8m) | ❔ estimate | None of the three GST supplies ships with a mains cord. Price from the search page, exact item not pinned. |
| consumable | Molex Mini-Fit Jr 6-pin receptacle + crimp terminals (mates the GST280 C6P plug) | 2 | 4.00 | 8.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/mini-fit%20jr%206) | ❔ estimate | Or cut the DC plug off (DC side only, never the mains side) and put ferrules on the 16 AWG leads. Check the pinout in the GST280A datasheet. |
| consumable | 4-pin power DIN panel jack (Kycon KPJX-4S class), mates the GST120A R7B plug | 1 | 4.00 | 4.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/kpjx-4s) | ❔ estimate | Or cut the DC plug off (DC side only, never the mains side) and put ferrules on the leads. Check the R7B pinout (2 pins +12 V, 2 pins GND) in the GST120A datasheet. Up to 8.5 A: a 5.5 x 2.5 barrel adapter is not rated for that. |
| consumable | Elecrow UART TTL to RS485 converter, half duplex, 3.3-5 V (Modbus to the DPS) | 3 | 1.90 | 5.70 | [Berrybase](https://www.berrybase.de/en/search?search=CIA00485T) | ❔ estimate | One at each DPS UART, one at the Pico: one RS-485 bus, 120 Ohm at both ends (WIRING.md). If the module switches direction itself, GP6 (DE) stays unused. Price (1.90 EUR) seen in a related-items block. |
| consumable | DC-DC buck converter 12 V to 5 V, >= 3 A (powers Pico 2, ESP32-S3, sensors) | 1 | 6.00 | 6.00 | [Berrybase](https://www.berrybase.de/en/search?search=step%20down%205V%203A) | ❔ estimate | Fed from the 12 V aux supply. Pico 2 via VSYS, ESP32-S3 via its 5 V pin, flow and level sensors, the OR gate; common GND at the star point. |
| consumable | 4-channel logic-level MOSFET switch module (3.3 V input, >= 5 A per channel) | 2 | 7.00 | 14.00 | [Amazon.de](https://www.amazon.de/s?k=4+kanal+mosfet+modul+3.3V) | ❔ estimate | 8 low-side channels: per zone the relay coil (GP10/GP16), both polarity coils (GP11/GP17), pump (GP12/GP18), fans (GP13/GP19). Add the external 4.7 k pull-downs (board.rs, erratum E9); do not rely on the module's own. |
| consumable | 1N5408 rectifier diode (flyback across each relay coil, pack of 10) | 1 × 10 | 1.50 | 1.50 | [Reichelt](https://www.reichelt.de/de/de/shop/search/1n5408) | ❔ estimate | 1N4007 works as well for 12 V relay coils. Skip if the relays you buy have a built-in diode (then mind the coil polarity). |
| consumable | Pin header set for Raspberry Pi Pico | 1 | 0.50 | 0.50 | [Berrybase](https://www.berrybase.de/en/search?search=RPIP-PINH) | ❔ estimate | BerryBase RPIP-PINH, 0.50 EUR seen on berrybase.at. |
| consumable | Resistor 10 kOhm 1/4 W (pull-ups / pull-downs, pack of 100) | 1 × 100 | 1.50 | 1.50 | [Reichelt](https://www.reichelt.de/de/de/shop/search/metallschicht%2010k) | ❔ estimate |  |
| consumable | Resistor 4.7 kOhm 1/4 W (MOSFET gate pull-downs, DS18B20 pull-up; pack of 100) | 1 × 100 | 1.50 | 1.50 | [Reichelt](https://www.reichelt.de/de/de/shop/search/metallschicht%204,7k) | ❔ estimate | RP2350 erratum E9: the 8 driver-input pull-downs must be <= 8.2 k, so 4.7 k (board.rs). |
| consumable | 1N5819 Schottky diode (Pico VSYS / ESP32 5 V OR-ing, pack of 10) | 1 × 10 | 1.00 | 1.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/1n5819) | ❔ estimate | Lets USB and the 5 V buck feed the boards without back-feeding each other. |
| consumable | Resistor 120 Ohm (RS-485 termination) + 2.2 k / 3.3 k (spare dividers for 5-12 V signals) | 1 | 1.00 | 1.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/metallschicht%20120) | ❔ estimate |  |
| consumable | Perfboard 160 x 100 mm + 2-pin/3-pin PCB screw terminals (5.08 mm, ~20 pcs) | 2 | 9.00 | 18.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/lochrasterplatine) | ❔ estimate | Two boards: one for the Pico/ESP32/ADS/RS-485, one for the 8 driver channels and the level OR gate. |
| consumable | Raspberry Pi Debug Probe (optional, for defmt logs and flashing) | 1 | 12.20 | 12.20 | [Berrybase](https://www.berrybase.de/en/raspberry-pi-debug-probe) | 🟡 listing | Optional; a second Pico 2 with debugprobe firmware works too. WIRING.md bring-up step 1 uses it. |
| consumable | Single-core flexible wire H07V-K 2.5 mm2, red, per m (TEC path) | 10 | 0.80 | 8.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/h07v-k%202,5) | ❔ estimate | Each zone's TEC path carries up to 18-20 A: >= 2.5 mm2 from DPS through fuse and relays to the TECs. |
| consumable | Single-core flexible wire H07V-K 2.5 mm2, black, per m (TEC path) | 10 | 0.80 | 8.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/h07v-k%202,5) | ❔ estimate |  |
| consumable | Stranded hook-up wire 0.25-0.5 mm2, assorted colours (signals, coils, sensors) | 1 | 12.00 | 12.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/litze%200,25) | ❔ estimate |  |
| consumable | WAGO 221-415 lever connector, 5-conductor, up to 4 mm2 | 15 | 0.95 | 14.25 | [Reichelt](https://www.reichelt.de/de/de/shop/produkt/verbindungsklemme_5-leiteranschluss-149800) | ❔ estimate | Price not shown in the fetched page. Use for the 24 V / 12 V / GND star point. |
| consumable | Knipex ferrule assortment, insulated, 0.5-2.5 mm2 (400 pcs) | 1 | 14.10 | 14.10 | [Reichelt](https://www.reichelt.de/de/de/shop/produkt/aderendhuelsen-sortiment_isoliert_0_5_-_2_5_mm_-222111) | 🟡 listing |  |
| consumable | Dupont jumper wires F-F / M-F (40 each) and heat-shrink assortment | 1 | 8.00 | 8.00 | [Berrybase](https://www.berrybase.de/en/search?search=jumper%20kabel) | ❔ estimate |  |
| consumable | TEC sandwich mounting: M3/M4 threaded rod, nuts, springs, 3 mm aluminium backplate | 8 | 5.00 | 40.00 | [Amazon.de](https://www.amazon.de/s?k=gewindestange+m4+edelstahl+federn+set) | ❔ estimate | Even clamping pressure on the ceramic; insulating washers so the block and cooler are not shorted through the screws. |
| consumable | Arctic MX-6 thermal paste, 4 g | 2 | 6.90 | 13.80 | [Caseking](https://www.caseking.de/en/search?search=arctic%20mx-6) | ❔ estimate | 16 TEC faces + NTC beads. |
| consumable | Barbed hose reducer 10 mm to 6 mm, straight (13/10 loop to the YF-S401) + 20 cm 6 mm ID tube + clamps | 4 | 2.50 | 10.00 | [Amazon.de](https://www.amazon.de/s?k=schlauchverbinder+reduzierst%C3%BCck+10mm+6mm) | ❔ estimate | Keep 5 cm of straight tube before the sensor. Plastic (PP/POM) reducers, no aluminium. |
| consumable | Alphacool Eiszapfen 13/10 mm compression fitting G1/4, deep black, six-pack | 4 × 6 | 35.62 | 142.48 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/fittings/compression-fittings/alphacool-eiszapfen-13/10mm-compression-fitting-g1/4-deep-black-sixpack) | 🟡 listing | Two loops: reservoirs, pump outlets, flow sensors, T-adapters, cold-plate reducers; spares for the bed stage. Brass. |
| consumable | G1/4 T-adapter (3x inner thread), for the inline water temperature sensor | 2 | 5.00 | 10.00 | [Alphacool](https://shop.alphacool.com/en/shop/fittings) | ❔ estimate |  |
| consumable | Phobya EPDM tube 13/10 mm, black, per m | 16 | 4.49 | 71.84 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/fittings/compression-fittings/alphacool-eiszapfen-13/10mm-compression-fitting-g1/4-deep-black-sixpack) | 🟡 listing | Price shown as recommended accessory on the fittings page. Per zone: 3 m loop + 5 m coiled in that zone's bench container. Check per-m vs per-pack unit at checkout. |
| consumable | Reducers / short 10/8 mm tube and hose clamps to the cold-plate barbs | 2 | 10.00 | 20.00 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/fittings/quick-release-fittings) | ❔ estimate | Cold plates in series; match the barb OD of the blocks you receive. |
| consumable | Aqua Computer Double Protect Ultra, 5 l canister (ready-mixed coolant with inhibitor) | 2 | 32.90 | 65.80 | [Aqua Computer](https://shop.aquacomputer.de/Water-Cooling/Coolant/Double-Protect-Ultra-5l-canister::3127.html?language=en) | 🟡 listing | One canister per loop + mat. Replace yearly. |
| consumable | Distilled water 5 l (flushing and leak test) | 2 | 3.00 | 6.00 | [Amazon.de](https://www.amazon.de/s?k=destilliertes+wasser+5l) | ❔ estimate | Any drugstore. The bench container (10 l) can be plain tap water: the coil keeps it out of the loop. |
| consumable | Self-adhesive closed-cell insulation tape (Armaflex type), 3 mm x 50 mm x 15 m | 2 | 12.00 | 24.00 | [Aquatuning](https://www.aquatuning.com/en/aquaristics) | ❔ estimate | Wrap 8 cold plates and the short lines against condensation (02-electrical-safety.md). |
| consumable | Electronics enclosure, ABS ~300 x 250 x 120 mm (dry compartment, above water level) | 1 | 35.00 | 35.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/kunststoffgeh%C3%A4use%20abs) | ❔ estimate | Bigger than the Solo box: two DPS modules (or the carrier), 6 relays, two fuse holders. |
| consumable | Drip tray: plastic storage tray ~80 x 60 cm, low rim (both loops and the leak cable) | 1 | 15.00 | 15.00 | [Amazon.de](https://www.amazon.de/s?k=auffangwanne+kunststoff+80x60) | ❔ estimate |  |

### Control

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`control_mcu`](../PARTS.md) | Raspberry Pi Pico 2 (RP2350), SC1631 | 1 | 4.90 | 4.90 | [Reichelt](https://www.reichelt.com/de/en/shop/product/raspberry_pi_pico_2_rp235x_cortex-m33_microusb-383358) | 🟡 listing | Without headers; see the pin-header line. |
| [`temp_sensors`](../PARTS.md) | Alphacool Eiszapfen temperature sensor flat G1/4, 10k NTC (water, return line) | 2 | 10.98 | 21.96 | [Alphacool](https://shop.alphacool.com/en/shop/controllers-and-sensors/temperature-sensor/sen-alphacool-eiszapfen-temperature-sensor-flat-g1/4-black) | 🟡 listing | ADS ch0 (zone 0) and ch2 (zone 1). One per loop, in the T-adapter in the return line. B value not published: calibrate in an ice bath and at ~40 C. |
| [`temp_sensors`](../PARTS.md) | 10k NTC epoxy bead thermistor, B ~3950, with leads (TEC hot face, 2 + 2 spares) | 4 | 1.20 | 4.80 | [Reichelt](https://www.reichelt.de/de/de/shop/search/ntc%2010k) | ❔ estimate | ADS ch1 (zone 0) and ch3 (zone 1): one per zone on the heatsink base of an inner TEC, clamped with thermal paste. Calibrate like the inline sensors. |
| [`temp_sensors`](../PARTS.md) | Adafruit SHT45 breakout (room temperature / humidity for the dew-point guard) | 1 | 13.00 | 13.00 | [Berrybase](https://www.berrybase.de/en/search?search=SHT45) | ❔ estimate | Read by the ESP32-S3 hub (02-electrical-safety.md, Condensation). |
| [`thermal_cutoff`](../PARTS.md) | Bimetal thermostat, normally closed (Oeffner), 50 C, auto-reset (cold plates) | 8 | 2.98 | 23.84 | [sensorshop24](https://www.sensorshop24.de/bimetall-temperaturschalter-thermostat-oeffner-schliesser) | 🟡 listing | One per cold plate (8). Select Oeffner + 50 C. Uncertified. Test every unit with a hot-air gun and a thermometer. |
| [`thermal_cutoff`](../PARTS.md) | Bimetal thermostat, normally closed (Oeffner), 80 C, auto-reset (heatsink bases) | 8 | 2.98 | 23.84 | [sensorshop24](https://www.sensorshop24.de/bimetall-temperaturschalter-thermostat-oeffner-schliesser) | 🟡 listing | One per cooler base (8). Select Oeffner + 80 C. Each zone's eight cutoffs in series in that zone's relay-coil circuit (12 V, coil current only). |
| [`leak_sensor`](../PARTS.md) | HW group Sensor WLD Relay 1W-UNI (incl. 2 m WLD sensing cable A) | 1 | 95.00 | 95.00 | [BellEquip (AT)](https://www.bellequip.at/produkte/sensoren-wasser-und-leckage/sensor-wld-relay-1w-uni-hw-group-wassleck-detektor-mit-relais-ausgang) | ❔ estimate | One for the whole hub (GP21). Relay output signals water OR disconnected cable. Price not shown on the page. Wire the contact so dry = LOW at GP21 with the 10 k pull-up (WIRING.md). Kept for the open-wire detection (see the Solo list for the cheaper options checked and rejected). |
| [`temp_sensors`](../PARTS.md) | ADS1115 4-channel 16-bit ADC breakout | 1 | 5.60 | 5.60 | [Berrybase](https://www.berrybase.de/en/search?search=ADS1115) | 🟡 listing | Address 0x48 (ADDR to GND). All four channels used: ch0/ch1 zone 0, ch2/ch3 zone 1 (board.rs NTC_CHANNELS). |
| [`temp_sensors`](../PARTS.md) | Metal film resistor 10 kOhm 0.1 % (NTC divider references) | 6 | 0.40 | 2.40 | [Reichelt](https://www.reichelt.de/de/de/shop/search/10k%200,1%25) | ❔ estimate | 4 used (ch0-ch3) + 2 spares. Not the same as the generic 10 k pull resistors. |

### Hub

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`hub_controller`](../PARTS.md) | Espressif ESP32-S3-DevKitC-1-N8R8 | 1 | 18.90 | 18.90 | [Berrybase](https://www.berrybase.de/en/espressif-esp32-s3-devkitc-1-development-kit-esp32-s3-wroom-wifi-bluetooth-le-240mhz-5v-3-3v-01a0a08fef6771fab6d4b97a830c7c92) | ❔ estimate | 18.90 EUR (BerryBase ADA5336) seen in a related-items block; check the SKU is N8R8. Mouser EU lists it at ~11-13 EUR net. |

### Thermal

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`tec_module`](../PARTS.md) | Peltier module 40 x 40 x 3.8 mm, 6.0 A, 15.4 V, 51.4 W (Reichelt TECB 1) | 8 | 28.40 | 227.20 | [Reichelt](https://www.reichelt.de/de/de/shop/produkt/thermo-modul_peltierelement_40x40x3_8mm-32052) | 🟡 listing | Sold singly; check that Reichelt has 8 (+ spares) in stock. Specs close to the TEC1-12706 the model uses; get the datasheet from the product page and compare Qmax/R. At 4.5-5 A per TEC they run well below Imax. |
| [`cold_plate`](../PARTS.md) | Copper water block 40 x 40 mm for Peltier modules, barbed ports | 8 | 10.00 | 80.00 | [Amazon.de](https://www.amazon.de/s?k=kupfer+wasserk%C3%BChlblock+40x40) | ❔ estimate | Copper, not aluminium (no mixed metals). Barbs are ~8 mm OD: see the reducer line. Lap flat if needed. |
| [`heatsink`](../PARTS.md) | Thermalright Peerless Assassin 120 SE dual-tower cooler (2x 120 mm PWM, 0.20 A each) | 8 | 43.90 | 351.20 | [Caseking](https://www.caseking.de/en/brands/thermalright) | 🟡 listing | One per TEC. The kit assumes 0.07 K/W per zone, i.e. <= 0.28 K/W per cooler with 4 in parallel. Four of the Solo list's single-tower Arctic Freezer 36 CO (0.11 K/W for 3, ~0.33 K/W each) would give ~0.083 K/W per zone, so the Duo list uses a dual tower. Its real K/W on a 40 x 40 TEC is unmeasured: measure it. Fans are not rated for 24/7 like the Arctic CO fans. Socket mounts do not fit a TEC: see the mounting line. |
| [`pump`](../PARTS.md) | Alphacool Laing DDC310 Single Edition, silver (12 V, tach) | 2 | 68.58 | 137.16 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/pumps/laing-ddc/ddc-pumps/alphacool-laing-ddc310-single-edition-silver) | 🟡 listing | One per zone (GP12 / GP18). Pump without top: mounts into the Eisstation below. Speed set by the firmware (25 kHz PWM on the switched supply; 100 % while priming or on low flow). Tach to a Pico input via the 10 k pull-up. |
| [`reservoir`](../PARTS.md) | Alphacool Eisstation DDC - Solo reservoir (mounts directly on the DDC pump, G1/4) | 2 | 34.63 | 69.26 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/reservoirs/reservoir-without-pump/for-ddc/alphacool-eisstation-ddc-solo-reservoir) | 🟡 listing | One per zone: the two zones run at different temperatures, so they get separate loops (a shared reservoir would mix them). Plastic wall, so the capacitive level sensor works. See the OR-gate line for the single level input. |
| [`reservoir`](../PARTS.md) | XKC-Y25-NPN non-contact capacitive level sensor, 5-12 V (LOW_WATER) | 2 | 8.00 | 16.00 | [Amazon.de](https://www.amazon.de/s?k=XKC-Y25-NPN) | ❔ estimate | One per reservoir, both into GP22 through the OR gate. Power at 5 V and measure the idle output before connecting. Wanted per sensor: LOW = water present, HIGH = low water or broken wire (WIRING.md). |
| [`reservoir`](../PARTS.md) | 74HCT32 quad 2-input OR gate, DIP-14, + socket (combines the two level sensors into GP22) | 1 | 0.80 | 0.80 | [Reichelt](https://www.reichelt.de/de/de/shop/search/74hct32) | ❔ estimate | board.rs reads ONE level input (GP22) but each zone has its own reservoir. Power the gate at 5 V, give each input a 10 k pull-up to 5 V (open sensor wire = HIGH = fault) and feed the output to GP22 (through the 2.2 k / 3.3 k divider on perfboard; the carrier's LEVEL input is 5 V-safe). Either reservoir low, or a broken wire, reads HIGH = LOW_WATER. Open item: not in WIRING.md yet. |
| [`flow_sensor`](../PARTS.md) | YF-S401 hall flow sensor, 98 Hz per L/min, 7 mm barbs (for 6 mm ID hose) | 2 | 4.00 | 8.00 | [TinyTronics (NL, ships to DE)](https://www.tinytronics.nl/en/sensors/liquid/yf-s401-water-flow-sensor) | 🟡 listing | One per zone (GP14 / GP20). Matches the prebuilt UF2: FLOW_HZ_PER_LPM = 98. Range 0.3-6 L/min, +-10 %: calibrate with a measuring jug. Power at 5 V; measure the idle level before connecting. Flow direction arrow matters. |

### Bench rig

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| bench | Insulated cool box ~10 l (thermal load: the 'sleeper' for bench tests) | 2 | 25.00 | 50.00 | [Amazon.de](https://www.amazon.de/s?k=k%C3%BChlbox+10l+passiv) | ❔ estimate | One per zone, filled with water; that zone's 5 m tube coil lies in it. |
| bench | DS18B20 waterproof temperature probe, 1 m cable (bath temperature, logged by the hub) | 2 | 3.50 | 7.00 | [Berrybase](https://www.berrybase.de/en/search?search=DS18B20%20wasserdicht) | ❔ estimate | One per bench container, on the ESP32-S3 (ESPHome dallas) with one 4.7 k pull-up on the bus. |
| bench | Power resistor 1 Ohm, >= 100 W, aluminium housing (DPS bring-up dummy load) | 1 | 8.00 | 8.00 | [Reichelt](https://www.reichelt.de/de/de/shop/search/hochlastwiderstand%201%20ohm) | ❔ estimate | WIRING.md bring-up step 3: test the DPS on a 1 Ohm load before any TEC, set to 1-2 A from the DPS front panel (not from the Pico, which would request up to 15 A = 225 W into 1 Ohm). Mount on a heatsink. |

**Subtotal bench: 2,225.87 EUR**

## Stage 2: bed (add to the bench build)

### Water mat

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`quick_disconnect`](../PARTS.md) | Koolance QD3 no-spill female, straight, 13/10 mm, black | 4 | 22.98 | 91.92 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-water-cooling/fittings/quick-release-fittings/koolance-qd3-quick-disconnect-no-spill-female-straight-for-13/10mm-3/8-x-1/2-tubing-black) | 🟡 listing | ~0.2 ml freed per disconnect (Koolance spec). Hub side, supply + return per zone. |
| [`quick_disconnect`](../PARTS.md) | Koolance QD3 no-spill male, straight, 13/10 mm, black | 4 | 21.98 | 87.92 | [Aquatuning](https://www.aquatuning.com/en/koolance) | ❔ estimate | The 16/10 male is listed at 21.98 EUR; 13/10 assumed the same. Mat side. |
| [`water_mat`](../PARTS.md) | DIY mat: PVC tube 4 mm ID / 6 mm OD (fabric-reinforced if available), per m | 60 | 1.20 | 72.00 | [Amazon.de](https://www.amazon.de/s?k=pvc+schlauch+4mm+innen+6mm+au%C3%9Fen) | ❔ estimate | ~30 m per mat in parallel channels (parts.toml water_mat). 8 mm was too stiff in the documented build. |
| [`water_mat`](../PARTS.md) | DIY mat: foam topper 80-90 x 200 cm, ~4 cm (channels cut in), one per side | 2 | 45.00 | 90.00 | [Amazon.de](https://www.amazon.de/s?k=schaumstoff+topper+90x200+4cm) | ❔ estimate |  |
| [`water_mat`](../PARTS.md) | DIY mat: 1-to-8 manifold, 10 mm inlet to 8x 4 mm barbs (supply + return) | 4 | 12.00 | 48.00 | [Amazon.de](https://www.amazon.de/s?k=verteiler+messing+4mm+schlauch+8+fach) | ❔ estimate | Must be pressure-rated (brass or PP), not an aquarium air manifold. Parallel channels keep flow resistance low. |

### Consumables

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| consumable | Phobya EPDM tube 13/10 mm, black, per m (insulated bed lines, 4 x 3 m) | 12 | 4.49 | 53.88 | [Aquatuning](https://www.aquatuning.com/en/watercooling/custom-watercooling/fittings/compression-fittings/alphacool-eiszapfen-13/10mm-compression-fitting-g1/4-deep-black-sixpack) | 🟡 listing |  |
| consumable | Closed-cell tube insulation for 13 mm OD tube, 2 m pieces | 6 | 5.00 | 30.00 | [Amazon.de](https://www.amazon.de/s?k=armaflex+schlauch+13mm) | ❔ estimate | Against condensation and heat loss on the hub-to-mat lines. |

### Control

| Role | Item | Qty | Unit | Line | Shop | Status | Notes |
|---|---|---:|---:|---:|---|---|---|
| [`leak_sensor`](../PARTS.md) | HW group WLD sensing cable A, extra length for the hub-side couplings | 1 | 25.00 | 25.00 | [BellEquip (AT)](https://www.bellequip.at/produkte/sensoren-wasser-und-leckage/sensor-wld-relay-1w-uni-hw-group-wassleck-detektor-mit-relais-ausgang) | ❔ estimate | Optional: route under all four QD3 couplings; the included 2 m covers the drip tray. |

**Subtotal bed: 498.72 EUR**

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
