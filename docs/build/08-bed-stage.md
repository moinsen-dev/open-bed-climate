# Step 8: Bed stage

**Goal:** replace the bench bath with the water mat, route lines and cables safely, handle condensation, and sleep the
first night with conservative settings.

**Time:** 3–4 h, plus a second 24 h leak test and the first night.

> ⚠️ **Stop here unless:** every item in [step 7, section 3](07-bench-commissioning.md#3-safety-checklist-safetymd) passed,
> and **a qualified person has reviewed the electrical part** ([SAFETY.md](../../SAFETY.md)). This is a prototype that
> no one has slept on yet.

## Parts

| Role / item | Qty | Notes |
|---|---|---|
| `water_mat` | 1 | the hardest part to source (see the role notes); OPEN-DECISIONS D4 recommends buying a medical cooling pad for v0 |
| `quick_disconnect` (dry-break, ≤ 0.5 mL spill per disconnect) | 2 pairs | supply and return, at the hub |
| `temp_sensors`: SHT45 room temperature/RH on the hub | 1 | enables the dew-point guard |
| Waterproof mattress protector *(no role yet)* | 1 | under the mat |
| Foam tube insulation, cable/tube sleeve *(no role yet)* | | the line between hub and bed |

## Steps

### 8.1 Test the mat and couplings off the bed

1. Test each quick-disconnect pair over a dry paper towel: connect and disconnect five times with water in the line.
   The towel spot per disconnect must be tiny (role target **≤ 0.5 mL**). One DIY build reported couplings that did not
   self-seal (`01-thermal-fluidics.md`).
2. Lay the mat **flat on towels on the floor**. Drain the bench loop, take out the bench coil, and connect the mat with the
   quick disconnects (supply to the mat inlet, mat outlet → return line → water NTC → reservoir).
3. Fill and prime as in [step 5](05-water-loop.md#55-fill-and-prime-electronics-unpowered) (pump on its own 12 V, the
   rest unpowered). Press gently along the mat channels to move trapped air toward the outlet.
4. **24 h leak test with the mat**, paper towels on every connection and under the mat. The bench test doesn't cover the
   mat, its fittings or the couplings.

### 8.2 Place the mat

1. Waterproof mattress protector on the mattress, then the mat under the sleeper's **torso and legs**, then a thin
   topper or fitted sheet on top. The mat must lie flat: no folds, no tube crossing under a hip or shoulder where body
   weight could pinch it shut (`water_mat`: parallel channels resist pinch-off better than one long serpentine).
2. Lead the mat lines off the bed at the **foot end or the side next to the hub**, where nobody lies on them.

### 8.3 Hub, lines and cables

1. The hub stands on the floor next to the bed **in its drip tray**, electronics above the water parts, as on the bench.
   Keep it ventilated: the heatsink fans need free air.
2. Supply and return line from the hub to the mat: insulated, strain-relieved at both ends, no kinks, not trapped by
   the bed frame or a bed leg. Run them in a sleeve along the floor, away from where you walk.
3. Leak sensing: the leak cable stays in the hub tray, under the couplings. `02-electrical-safety.md` also wants a
   sensor at the cover edge; with one leak input (GP21) you can extend the same sensing cable to under the mat's
   connection point if your module supports the length. Note what you did.
4. **No mains and no TEC power goes near the bed.** Only water lines (and, later, SELV sensing cables) reach the mat.
5. Re-prime with the loop in its final position and the mat on the bed: air collects at the highest point (the mat).
   Run the pump (Prime, repeatedly) until no bubbles return to the reservoir. Top up.

### 8.4 Condensation and dew point

Below the room's dew point the mat and lines sweat (`02-electrical-safety.md`, Condensation).

1. Configure the room sensor on the hub (`room_temperature` / `room_humidity`, see [step 6](06-software.md#room-sensor-strongly-recommended-before-stage-b)).
   The hub's **dew-point guard** then raises any cooling setpoint below 16 °C to at least dew point + 1 K.
2. Know your numbers. Dew point at 22 °C room: ≈ 11 °C at 50 % RH, ≈ 14 °C at 60 % RH, ≈ 16 °C at 70 % RH.
3. The Solo Starter is modelled to reach ~21.7 °C water with a sleeper in a 25 °C room, so it will rarely get near the
   dew point while you lie on it. **Pre-cooling** an empty bed in a cool, humid room can.
4. For the first nights put a dry paper towel under one corner of the mat and around the hub-side couplings. Damp in the
   morning = condensation or a leak; find out which.

Condensation at 15 °C water and 60 % RH is open measurement item 5 in [OPEN-DECISIONS.md](../design/OPEN-DECISIONS.md).

### 8.5 Before the first night (awake, nearby)

1. **SAFETY.md checklist item 5 on the bed:** one full warm cycle to 43 °C and one full cool cycle on the **empty bed**,
   while you are awake and nearby. Measure the mat surface with your reference thermometer under the sheet.
2. Lie on the bed for an hour in the evening with the zone running, phone at hand.
3. In Home Assistant, create an automation that **notifies your phone** when "Left problem" turns on or "Control board
   link" turns off.

### 8.6 First night: conservative settings

These are this guide's recommendations for a first night, not firmware limits (those stay at 13–43 °C).

- Keep the target between **20 °C and 34 °C**. The default night program on the hub (24 → 21 → 20 → 23 → 25 °C, wake
  ramp to 32 °C) fits inside this range. Turn it on at bedtime.
- Phone at the bedside, with the problem notification on.
- Smoke detector in the bedroom.
- Hub on the floor in its tray, power strip switch reachable from the bed.

⚠️ Don't use the system for anyone who can't react to discomfort or can't feel heat well (infants, people with reduced
sensation). Prolonged contact at moderate temperatures can cause low-temperature burns; that is why the setpoint is
capped at 43 °C.

## What to watch

| During the night (HA history, next morning) | Healthy | Act if |
|---|---|---|
| Water temperature vs. target | follows within ~1 °C after the first 30 min | drifts away for long periods: cooling capacity too low |
| Heatsink temperature | well below 60 °C | approaches 75 °C (trip) |
| Flow | steady, ≥ 0.4 L/min | drops or fluctuates: air in the mat, or a pinched line |
| Fault code | 0 all night | anything else: decode with the table in [step 6](06-software.md#fault-code) |
| Noise | you sleep | fans too loud: bedroom target ≤ 30 dB(A) at 1 m; PWM fan control is not in the firmware yet |
| Paper towels, under the mat, hub tray | dry | damp: leak or condensation; stop until you know which |
| Comfort | — | write down how the temperatures felt; this is data too |

## ✅ Checkpoint

- [ ] Mat + couplings passed a 24 h leak test.
- [ ] Warm and cool cycle on the empty bed done, mat surface temperature measured.
- [ ] Dew-point guard active (room sensor values visible in HA).
- [ ] Problem notification tested (unplug the hub UART briefly; your phone gets the alert).
- [ ] First night done, history exported, towels dry.

## If it fails

- **Flow drops when you lie down:** body weight pinches a channel or line. Re-route the lines, or move the mat so no
  manifold or tube lies under a hip or shoulder.
- **Bubbles keep coming back:** air trapped in the mat. Prime longer, lift the mat's outlet end above the rest while
  priming.
- **The bed never gets cool enough:** expected limits first: ~21.7 °C water with a sleeper in a 25 °C room (model).
  Pre-cool the empty bed before bedtime. Your bench R_hs result tells you if the heatsink is the bottleneck.
- **It's too warm under the sheet even at 20 °C water:** the mat-to-body heat transfer is lower than the model's
  6 W/K guess. That number (UA body↔water, open measurement item 1) is one of the most valuable things to report.

Then [submit a build report](07-bench-commissioning.md#8-submit-a-build-report) with the bed results.
