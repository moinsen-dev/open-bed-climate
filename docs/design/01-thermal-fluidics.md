# Thermal & Fluidics

All numbers come from the lumped model in `software/obc/src/obc/thermal.py`. They are **first-order estimates**
until a prototype is measured. Re-run the sweep after changing any parameter.

## Model
- TEC: TEC1-12706, with parameters **fitted to its datasheet maxima** (Qmax 50 W, ΔTmax 66 K, Vmax 14.4 V at
  Imax 6.4 A, 25 °C hot side): S = 0.0453 V/K, R = 1.78 Ω, K = 0.467 W/K (`TecModule.from_datasheet`). For a different TEC,
  enter its datasheet values; the test suite checks that the fit reproduces them.
- Water loop per side: 1.2 kg water + 800 J/K hardware → C ≈ 5.8 kJ/K.
- Sleeper load: UA body↔water 6 W/K at skin 34 °C (≈ 50–80 W into the bed when cooling). Room losses 2.5 W/K.
- Cold plate: 12 W/K per TEC. Heatsink: R per side (fans on).

## Sizing sweep (25 °C room, sleeper in bed, best-case current)

| TEC/side | Heatsink R (K/W/side) | Coldest water | TEC power/side | Hot face |
|---|---|---|---|---|
| 2 | 0.11 | 23.5 °C | 143 W | 48 °C |
| 3 | 0.11 | 21.5 °C | 189 W | 55 °C |
| 3 | 0.07 | 20.1 °C | 217 W | 47 °C |
| 3 | 0.05 | 19.3 °C | 213 W | 41 °C |
| **4** | **0.07** | **18.2 °C** | **250 W** | **51 °C** |
| 4 | 0.05 | 16.9 °C | 291 W | 46 °C |

**Design point (Duo): 4 TECs per zone, heatsink ≤ 0.07 K/W per zone, current capped at 4.5 A per TEC** (see below).
Pod 6 publicly uses 3 TECs per side. With TEC1-12706-class modules our model needs 4 to reach a similar range,
so Pod 6 probably uses larger modules; that is not public. The Solo Starter kit uses 3 TECs at 0.11 K/W.
Contributions with stronger modules (e.g. 12710/12715 class) are welcome: add their datasheet values and a kit.

Implications:
- Under full sleeper load in a warm room, cooling bottoms out around 18–19 °C. The 13 °C end of the range is
  reachable only in a cooler room or with the bed unoccupied (pre-cooling). Pre-cooling before bedtime is the
  practical answer. The UI must show this honestly.
- Heating is easy: TECs in reverse run at COP > 1. The constraint is the TEC water-side face, which runs about
  q/(12 W/K) above the water. Without a limit it reaches ~48 °C while heating to 43 °C. The controller therefore
  tapers heating current (0.5 A/K below 48 °C water). Simulated peak face is 45.3 °C, and 43 °C is reached in 7–12 min
  (all kits are tested in 16 °C and 22 °C rooms).
- The heatsink is the main design lever. 0.07 K/W per side means a pair of tower-cooler-class fin stacks with
  120 mm fans. Two-sided placement with fans between them (as in Pod 6's public description) is a good layout.

## Current cap: the cheap win
Cooling power has strongly diminishing returns above ~4.5 A per TEC (4 TECs, 0.07 K/W):

| A per TEC | Coldest water | TEC power/zone |
|---|---|---|
| 3.5 | 19.8 °C | 101 W |
| 4.0 | 19.1 °C | 132 W |
| **4.5** | **18.6 °C** | **167 W** |
| 5.0 | 18.3 °C | 207 W |
| 6.0 | 18.2 °C | 298 W |

The Duo Standard kit therefore caps at 4.5 A (`max_tec_current_a`). It loses 0.4 K versus 6 A but uses 44 % less
power, so each zone fits one certified 280 W supply. The cap is a firmware limit (`Kit.controller()`) **and** the
current limit written to the TEC driver. Tests run a full pull-down in a 30 °C room and check the supply stays under 80 %.

## Lessons from earlier DIY builds (public)
- opencooler V1 (Hackaday 205182, June 2026): cooling was too weak; one TEC side got warm. Heat rejection was undersized.
- TechTeamGB (2024): heating worked better than cooling; quick disconnects didn't self-seal.
- Several builds drove TECs with raw PWM (capacitors ran hot). Open Bed Climate requires smooth DC.

All of this is consistent with our model: cooling is the hard part, and the heatsink is the main lever.

## Water loop
- Flow: 0.4–0.6 L/min per side. Q = ṁ·cp·ΔT gives ΔT ≈ 2 K at 70 W, so cover temperature is even.
- Pump: 12 V brushless DC centrifugal pump with a tach output, ~1 m head, ≤ 5 W. A tach is mandatory:
  TECs stay off until flow is confirmed, and the MCU raises `NO_FLOW` after a 20 s grace period.
- Reservoir: about 0.5 L internal reservoir with a fill port at the top, plus a capacitive level sensor
  (non-contact on the wall). Low level → `LOW_WATER`: TECs off, pump off.
- Cold plates: aluminium (anodized) or copper water blocks, 40×40 mm per TEC. Use a corrosion inhibitor
  (distilled water + glycol/biocide) and avoid mixing copper and aluminium in the same loop.
- Cover: TPU-laminated channel mat (welded TPU film, similar to medical cooling pads), 4 lines in the umbilical
  (supply/return × 2). Self-sealing quick couplings (CPC dry-break type) at the hub so unplugging doesn't spill.
- Priming: pump runs with TECs off until flow and level are stable. Air purge through the reservoir.

## Open measurement items
- Real UA body↔water through mattress topper fabric (sets everything else). Measure on the first prototype
  with a heated dummy (resistive pad at 34 °C).
- TEC cold-plate thermal resistance with real paste and clamping.
- Heatsink R vs fan noise at night (bedroom target ≤ 30 dB(A) at 1 m).
