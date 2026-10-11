# Open decisions & measurements

| # | Question | Recommendation | Blocks |
|---|---|---|---|
| D1 | Licenses | **Decided 2026-10-10:** hardware CERN-OHL-S-2.0, software and docs Apache-2.0 | — |
| D2 | Control MCU | **Decided:** Raspberry Pi Pico 2 (RP2350) in both tiers. It is a standard part, cheap and easy to flash. Revisit STM32G4 only if the Tier 1 power board needs HRTIM-class PWM. | — |
| D3 | Hub | **Decided:** ESP32-S3 with ESPHome as the Tier 0 default (Home Assistant native); Raspberry Pi as an option for heavier biometrics | — |
| D4 | Cover mat: buy a medical cooling pad for v0 vs custom TPU weld | Buy one for v0 to measure UA body↔water early | thermal validation |
| D5 | Vibration alarm in v1? | Yes, an ERM motor on the cover board is cheap | cover PCB |
| D6 | Compatibility track: also support existing Pod 3–5 hardware by adopting the community-documented protocols (free-sleep / opensleep)? | Separate later track; keep OPL as our own protocol | — |

## Measurements needed from prototype 0
1. UA body↔water through a typical topper (heated dummy pad at 34 °C).
2. Cold-plate R per TEC with real clamping.
3. Heatsink R vs fan noise, target ≤ 30 dB(A).
4. Piezo SNR per grid position (HR detectability across sleeping positions).
5. Condensation behaviour at 15 °C water and 60 % RH.

## Pod 6–specific reverse engineering (deferred)
Requires owning a unit. FCC internal photos for 2AYXT61100005 become public around 2027-02-17; check them then
for the SoC, MCUs and cover-board layout.
