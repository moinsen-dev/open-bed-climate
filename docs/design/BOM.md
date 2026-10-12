# BOM v0.1: Duo Reference kit (Tier 1, queen, two zones), rough prototype quantities

> This is the **target** BOM once the Tier 1 power board and cover sensor board exist. What you can buy and build
> today is in [hardware/shopping/duo-reference.md](../../hardware/shopping/duo-reference.md) (about €2,860 incl. VAT).

For Tier 0 kits (modules only) see [`hardware/PARTS.md`](../../hardware/PARTS.md).

Prices are rough single-unit estimates (EUR) to show the order of magnitude, not quotes.

| # | Part | Qty | Example / class | ~EUR |
|---|---|---|---|---|
| 1 | 24 V ≥ 750 W certified PSU, enclosed, active PFC, inside the closed Tier 1 power module (mains side assembled by a qualified electrician) | 1 | Mean Well RSP-750-24 class (verify the current datasheet) | 90 |
| 2 | TEC 40×40, 127 couples | 8 (+2 spare) | TEC1-12706 class, preferably a quality brand | 50 |
| 3 | Water cold plates 40×40 | 8 | aluminium water blocks | 40 |
| 4 | Heatsink + 120 mm fan towers | 2 | ≤ 0.07 K/W per side at quiet RPM (to be verified) | 80 |
| 5 | BLDC pump 12 V with tach | 2 | DC40-class, 5 W | 40 |
| 6 | Reservoir + capacitive level sensor | 1 | 0.5 L, printed or off-the-shelf | 20 |
| 7 | Dry-break quick couplings | 4 pairs | CPC NS2/PLC series | 60 |
| 8 | Tubing, insulated | 2× 2 m ×2 | silicone 6/9 mm + foam sleeve | 25 |
| 9 | Cover water mat | 1 | welded TPU channel mat (custom, or a medical cooling pad for v0) | 150 |
| 10 | Power board (custom PCB) | 1 | 6× buck + H-bridge, 2× hot-swap controller + FETs, 2× relays, NTC inputs, pump/fan drivers | 130 |
| 11 | Control MCU | 1 | Raspberry Pi Pico 2 (RP2350) | 5 |
| 12 | Hub | 1 | ESP32-S3 dev board (ESPHome) or Raspberry Pi | 10–70 |
| 13 | Bimetal thermal cutoffs | 10 | 50 °C NC (one per cold plate ×8), 80 °C NC (heatsinks ×2) | 25 |
| 14 | Leak sensors | 2 | rope sensor + hub tray probe | 15 |
| 15 | Cover sensor board (custom PCB) | 1 | RP2040 + 3× ADS131M08 + isolated RS-485 | 60 |
| 16 | Piezo film strips | 18 | PVDF strips | 70 |
| 17 | Capacitive electrodes, conductive fabric | 6 | | 15 |
| 18 | NTCs 10k, SHT4x | ~16 + 1 | | 15 |
| 19 | Enclosure, drip tray, fasteners | 1 | sheet metal or printed + tray | 80 |
| | **Total (approx.)** | | | **~990–1,040** |

Distilled water + inhibitor/biocide (e.g. 5–10 % propylene glycol): small cost.
