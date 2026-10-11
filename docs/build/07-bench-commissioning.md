# Step 7: Bench commissioning and measurements

**Goal:** prove on the bench that every safety function works, then measure the numbers the thermal model only
estimates. This step is where prototype 0 becomes useful to everyone else.

**Time:** 4–6 h for commissioning, then 1–2 days of **attended** measurement runs.

> ⚠️ From here on the TECs get real power. Stay at the bench whenever the zone is enabled, keep the emergency switch
> (the power strip) within reach, and don't leave the build running unattended until section 4 is complete.

Expected values below assume the Solo Starter firmware (3 TECs, 5.0 A per TEC = 15 A zone current) and TEC1-12706-class
modules. The thermal values are **model estimates**: if you measure something different, that is a result, not a
failure, as long as no safety limit is crossed.

## 1. Before you start

- [ ] Steps 2–6 checkpoints all ticked; the 24 h leak test passed.
- [ ] A log sheet ready (paper or spreadsheet): time, bath reference temperature, room temperature, DPS U/I display,
      wall power, notes.
- [ ] Plug-in mains power meter between the power strip and the **24 V brick**. (A second one for the 12 V brick if
      you have it.)
- [ ] Room temperature source in Home Assistant (SHT45 on the hub, or any room thermometer you already have in HA).
- [ ] Bath temperature source: the DS18B20 probe on the hub, or your reference thermometer read by hand. The firmware's
      "Left water temperature" is the **loop** water coming back from the coil, not the bath.

## 2. Bring-up order

This expands the bring-up order in [`WIRING.md`](../../hardware/WIRING.md#bring-up-order-do-not-skip) for one zone.
The loop is already filled, so you test with **real flow** instead of simulated pulses.

### 2.1 Relays and Modbus without TEC power

**Pull the 20 A fuse.** The TEC path is now open; the DPS output goes nowhere.

1. Plug in the 24 V brick. The DPS powers up.
2. In Home Assistant, Left fault code drops from 256 to **0** within a few seconds (Modbus works).
3. Set the **Left** climate to **heat_cool, target 13 °C** (maximum cooling demand).

Expected sequence (watch and listen):

- [ ] Pump starts (GP12), fans start (GP13). Left flow rises to **≥ 0.15 L/min** (design target 0.4–0.6).
- [ ] DPS display: **U-set 14.00 V** (the voltage ceiling), then **I-set 15.00 A** (3 × 5.0 A), then **output ON**.
- [ ] Then the **zone relay clicks** (GP10 high). Not before the DPS output is on.
- [ ] Left TEC current in HA: **≈ 5.0 A** (per TEC; there is no load, so this is the *requested* value). DPS reads
      **0.00 A** at 14 V (open output).

> **DPS register check:** if the DPS shows I-set **1.50** or **150.0** instead of 15.00, the current scaling in
> `DPS_MAP` is wrong for your unit (`tec_drive` notes: unverified). **Stop**, set the climate to off, and report it.
> Same if U-set isn't 14.00.

4. Change the target to **43 °C** (heating).

- [ ] The **zone relay drops** first (DPS output off).
- [ ] **≥ 2 s later** the **polarity relay clicks** (GP11 high = heat). The firmware waits for a read-back below 0.1 A
      and the 2 s dead time.
- [ ] Then the DPS output turns on again and the **zone relay closes**.

5. Set the climate to **off**: DPS output off, zone relay drops, pump and fans stop.

### 2.2 Calibrate the flow reading (fuse still pulled)

The flow interlock is only as good as the flow reading. The firmware converts pulses with `FLOW_HZ_PER_LPM`; the
prebuilt image uses **98 Hz per L/min**, which fits the YF-S401 on the shopping list (±10 %). Other sensors need their
own factor. A sensor that **over-reads** is the dangerous case: a dying pump would
still look healthy to the interlock.

1. Run the jug test ([M1](#m1-flow-rate-and-flow-sensor-factor)) now.
2. **Stop rule:** if Home Assistant's flow and the jug flow differ by more than **10 %**, make a source build with the
   corrected factor ([step 6](06-software.md#option-b-build-from-source)) and repeat the test **before you insert the
   fuse**.

- [ ] Jug flow and HA flow agree within 10 %. Flow ≥ 0.4 L/min (design 0.4–0.6).

### 2.3 First TEC power

1. Climate off. Unplug the 24 V brick, wait 10 s, **insert the 20 A fuse**, plug the brick back in.
2. Set **heat_cool, 13 °C**. Watch for 2 minutes with a hand near the emergency switch.

- [ ] DPS in constant-current mode: **I ≈ 15.0 A**, **U ≈ 10–12 V** (TECs need ~11.5 V at 5 A each; `tec_psu` notes).
- [ ] Left water temperature starts to fall (slowly: 10 L), heatsink temperature rises.
- [ ] Cold plates feel cold through the insulation edge; heatsinks warm; fans running.
- [ ] Wall power on the 24 V brick: **roughly 190–250 W** (estimate: ~165–210 W DPS output, plus brick and DPS
      losses). Must stay **≤ 280 W**; the kit is sized for ≤ 80 % of the brick.
- [ ] After 2 min: fuse holder, relay terminals and the TEC busbars are at most hand-warm. Nothing smells.

If the heatsink temperature climbs faster than ~1 °C every 10 s or passes **60 °C** in the first minutes, turn the
climate off: the heatsink contact or fans are not right.

## 3. Safety checklist (SAFETY.md)

This is the [SAFETY.md commissioning checklist](../../SAFETY.md#commissioning-checklist-before-the-first-night) plus
the other protection layers, on the bench. **Every item must pass before stage B.**

### 3.1 Leak test
- [ ] Done in [step 5](05-water-loop.md): 24 h, all towels dry.

### 3.2 Cutoff test (do it with the fuse **pulled**)

With the fuse out, the zone relay closes but no TEC power flows, so you can heat a plate safely.

1. Climate heat_cool, 13 °C; wait until the zone relay has closed.
2. Heat **cold plate 1** with the hot-air gun, reference thermometer on the plate next to the cutoff.

- [ ] The **zone relay drops at ≈ 50 °C** (± 5 °C, the cutoff tolerance). Write the temperature down.
- [ ] As the plate cools below the cutoff's reset temperature (30–35 °C, depending on the part), the relay closes again
      (auto-reset).

3. Repeat for **cold plates 2 and 3**, and for **each heatsink** (relay drops at ≈ 80 °C).

### 3.3 Flow interlock (fuse in, TECs running)
1. Climate heat_cool, 13 °C, full current flowing.
2. Pinch the supply tube (or fold it) until flow drops.

- [ ] As soon as flow reads **< 0.15 L/min**, TEC current goes to **0** and the zone relay drops.
- [ ] After **20 s**, fault code **8** (`NO_FLOW`) appears; "Left problem" on. The pump keeps running.
- [ ] Release the tube: flow returns, the fault clears by itself (not latching), cooling resumes.

### 3.4 Heartbeat
1. Zone running at full current. Unplug the hub's power (or its UART wires). Start a stopwatch.

- [ ] Within **10 s** the zone relay drops and the DPS output turns off (`HOST_TIMEOUT`, 64). The pump keeps running.
- [ ] Reconnect the hub: within ~10 s the hub re-sends the target and cooling resumes.

### 3.5 Controller crash
1. Zone running. Briefly connect the Pico's **RUN** pin to GND (reset).

- [ ] The zone relay, pump and fans drop **immediately** (the external pull-downs hold the gates low).
- [ ] After release the Pico boots, turns the DPS output off first, then resumes.

### 3.6 Leak, level, sensor
- [ ] Wet the leak cable with a towel: **TECs and pump off**, fault **16** (latching). Dry it, press **Left clear
      faults**: normal again.
- [ ] Drain the reservoir below the level sensor: **TECs and pump off**, fault **128**. Refill: clears by itself.
- [ ] Unplug the hot-side NTC: TECs off, fault **32** (latching). Plug back, clear faults.

### 3.7 Optional: fan failure
The most likely real-world fault. Zone cooling at full current; **unplug the fans**. Watch the heatsink temperature.

- [ ] Firmware trip at **75 °C**: fault **4** (latching), TECs off. If it passes 78 °C without a trip, switch everything
      off with the power strip and investigate (the 80 °C bimetal is the next layer).

### 3.8 Full warm cycle and full cool cycle (attended)
- [ ] **Warm:** target 43 °C. The heating current tapers as the loop water approaches 43 °C (by 0.5 A per K below
      48 °C; e.g. ≈ 4 A per TEC at 40 °C, ≈ 2.5 A at 43 °C). The loop water settles at **43 °C** and never exceeds
      **45 °C**; the bath follows more slowly. No cutoff opens. Note the time for the loop to reach 43 °C, and the bath
      temperature at that moment.
- [ ] **Cool:** target 13 °C until the water temperature stops falling (this is measurement M3 below).

During heating the **heatsink becomes the cold side**: it can drop below room temperature and sweat. Watch for drips.

## 4. ✅ Commissioning complete

- [ ] All items in section 3 passed, with values in the build log.
- [ ] Nothing changed in the safety limits.

Only now may the bench build run unattended, and only after a qualified person has looked at the electrical part do
you move to [stage B](08-bed-stage.md).

## 5. Measurement protocol

These are the model's key unknowns (`01-thermal-fluidics.md`, `OPEN-DECISIONS.md`). Each measurement says what you
do, what you log and how to compute the result.

### Constants you need

- **Heat capacity of the bench:** C ≈ (m_bath + m_loop) · 4186 J/(kg·K) + C_hw, where m_bath is the bath water you
  weighed, m_loop the coolant in the loop (weigh what you poured in, ~1 kg), and C_hw ≈ 1–2 kJ/K for the coil, plates and
  fittings. For 10 kg + 1 kg: **C ≈ 47 kJ/K**. A 1 kJ/K error is ~2 %. This lumps loop and bath together, which is
  fine for slow changes (minutes to hours).
- **T_bath** from the bath probe (or by hand), **T_loop** = Left water temperature (return NTC).
- **Room temperature** T_room from Home Assistant.
- Units: temperatures in °C (differences in K), rates dT/dt in K/s (K/h ÷ 3600), power in W.

### M1: flow rate and flow-sensor factor
Run this in [section 2.2](#22-calibrate-the-flow-reading-fuse-still-pulled), before the first TEC power.

1. Climate off. Press **Prime water loop** (pump runs 60 s).
2. During the run, take the return line off the reservoir and hold it into the measuring jug for **15 s**; keep the
   reservoir topped up from a second jug. Put it back.
3. True flow F_true = volume (L) × 4 (per minute). Read Left flow in HA after it has been steady for 30 s (F_HA).

**Result:** F_true, and if F_HA differs by more than 10 %, the corrected factor
**FLOW_HZ_PER_LPM_new = 98 × F_HA / F_true** for a source build. Check that F_true ≥ 0.4 L/min (design 0.4–0.6) and
well above the 0.15 L/min interlock.

### M2: bath losses and pump heat (after M3)
Run it right after the cool-down (M3), while the bath is well below room temperature.

1. Climate **off**. Disconnect the pump from GP12 and power it directly from 12 V (as in the leak test), so the loop
   keeps circulating with the TECs off.
2. Log T_bath for 3–4 h as the bath warms back toward room temperature.
3. At three or more points on the curve, take the slope dT_bath/dt (K/s) and compute y = C · dT_bath/dt and
   x = T_room − T_bath.
   Fit a straight line y = UA_loss · x + P_pump.

**Result:** UA_loss (W/K, the bath's heat gain from the room) and P_pump (W, pump heat into the water).
Reconnect the pump to GP12 afterwards.

### M3: cool-down curve at full current
1. Start with the bath near room temperature, everything off for 1 h.
2. Climate heat_cool, **13 °C** (the controller saturates at 5.0 A per TEC). Note the start time.
3. Log every 15 min by hand: DPS U and I, wall power (and T_bath if you have no probe). Home Assistant logs the rest.
4. Run until T_bath changes by less than **0.2 K per 30 min** (steady state). With 10 L this takes hours.
5. Check that **Left TEC current stays at 5.0 A** for the whole run. If it drops, the target was reached or raised:
   with a room sensor on the hub, the **dew-point guard** raises cooling targets below 16 °C to dew point + 1 K (often
   15–17 °C in a humid room), and the loop water can reach that while the bath is still warmer. Check the hub's ESPHome
   log, and note it in your report; the run is then not a full-current run.

**Result:** the curves T_bath(t) and T_loop(t), and the cooling power at each point:

**Q_cold = C · (−dT_bath/dt) + UA_loss · (T_room − T_bath) + P_pump**

(the TECs remove what the water loses, plus what leaks in from the room, plus the pump heat). Report Q_cold at a few
bath temperatures, and the steady-state T_bath and T_loop with room temperature.

Bonus: **UA_coil ≈ Q_cold / (T_bath − T_loop)** is the coil's heat transfer (W/K). It is the bench cousin of the
model's body↔water coupling (6 W/K guessed, open measurement item 1), and tells you how much the coil itself limits
the bench result. There is no model prediction for this
exact bench setup yet; with your UA_loss the model in `software/opod` can be re-run against it (help wanted).

### M4: heatsink thermal resistance (from M3)
At steady state (or any point late in M3):

**R_hs = (T_heatsink − T_room) / (P_TEC + Q_cold)**, with P_TEC = U_DPS × I_DPS (output side).

**Result:** R_hs in K/W. The Solo kit assumes **0.11 K/W** (`heatsink_k_per_w`, an estimate). Note where the hot-side
NTC sits: it measures the heatsink base next to one TEC, not the TEC face. For orientation: with ~165 W TEC power and
~60 W cooling, 0.11 K/W means the heatsink runs ~25 K above room.

### M5: steady-state water temperature vs TEC current (optional, needs source builds)
Repeat M3 with a source build where `MAX_TEC_CURRENT_A` is **3.0** and **4.0** (lowering the cap is allowed, see
[step 6](06-software.md)). The model predicts strongly diminishing returns above ~4.5 A per TEC
(`01-thermal-fluidics.md`, current cap table, computed for Duo). Re-flash the `solo-starter` 5.0 A build afterwards.

**Result:** a small table: current per TEC → steady-state T_bath and T_loop, Q_cold, P_TEC, wall power.

### M6: power
- 24 V brick at the wall at steady state in M3: **P_wall,24**. With DPS output P_TEC: overall efficiency
  η = P_TEC / P_wall,24. Check that the brick output (≈ P_wall,24 × 0.93) stays **≤ 224 W** (80 % of 280 W).
- 12 V brick at the wall (pump, fans, electronics): the kit budget is **≈ 40 W**.
- If you have an oscilloscope: the DPS output ripple across the TEC busbars at 15 A. Current ripple ≈ V_ripple / 0.66 Ω;
  the `tec_drive` role requires **< 10 %** of the maximum current. Nobody has measured this yet.

### M7: noise and heating time
- Fan and pump noise at 1 m with a phone sound meter app (rough is fine): the bedroom target is **≤ 30 dB(A)**.
- Heating time from 3.8: loop to 43 °C, with the bath temperatures at start and at that moment, and the bath mass.

## 6. Logging with Home Assistant

1. **History** panel → add the entities: Left water temperature, Left heatsink temperature, Left TEC current, Left flow,
   Left fault code, your room temperature (and humidity) and the bath probe.
2. Pick the time range of the run. Use the **download** button to export the data as CSV.
3. Export soon: Home Assistant keeps detailed history for 10 days by default.
4. The example config averages the diagnostic sensors over 30 s. For slopes over minutes to hours that is fine.
5. Keep the hand-written DPS and wall-power values next to the CSV; they are not in Home Assistant.

## 7. If it fails

- **Zone relay never closes:** check in order: fault code (any bit blocks it), flow ≥ 0.15 L/min, DPS output actually
  on (Modbus OK, fault 256 absent), cutoff chain closed.
- **Fault 256 with the DPS powered:** RS-485 A/B swapped, missing termination, wrong Modbus address/baud on the DPS, or
  the comm adapter unpowered. A logic analyser trace of the Modbus traffic is a welcome contribution
  (`firmware/README.md`, help wanted).
- **DPS goes into CV (voltage-limited) at 14 V instead of 15 A:** TEC wiring resistance too high, or the TECs have a
  higher resistance than the datasheet. Measure the voltage at the TEC busbars vs. the DPS terminals.
- **Water stops cooling at a high temperature, heatsink very hot:** heat rejection is too weak; this was the failure of
  earlier DIY builds (`01-thermal-fluidics.md`). Your R_hs measurement is exactly the useful result.
- **A cutoff opens during normal cooling:** it is mounted on the wrong side or is faulty. Never bypass it.

## 8. Submit a build report

Open a **[Build report](https://github.com/moinsen-dev/open-bed-climate/issues/new?template=build-report.yml)**
issue (template: `.github/ISSUE_TEMPLATE/build-report.yml`). Even a partial build is valuable.

- **Kit file:** `hardware/kits/solo-starter.toml`
- **Parts you actually used:** by role id, with links; anything that differs from `parts.toml`.
- **Measurements:** paste this block and fill it in:

```
Bench setup: bath m_bath = __ kg in a cool box, __ m tube coil; loop coolant __ kg; room __ °C / __ %RH; T_bath from __
Firmware: release __ (UF2) / source build at commit __ ; NTC calibrated: yes/no ; FLOW_HZ_PER_LPM = __
M1 flow: F_true = __ L/min (HA showed __)
M2 bath: UA_loss = __ W/K, P_pump = __ W
M3 cool-down at 5.0 A/TEC: T_bath __ °C → steady __ °C after __ h (T_loop __ °C, room __ °C); Q_cold = __ W at __ °C, __ W at __ °C; UA_coil = __ W/K
M4 heatsink: T_hs = __ °C, P_TEC = __ W (U __ V, I __ A) → R_hs = __ K/W ; NTC position: __
M5 (optional): 3.0 A → T_bath __ °C ; 4.0 A → T_bath __ °C
M6 power: 24 V brick at wall __ W, 12 V brick at wall __ W, ripple __ (if measured)
M7 noise at 1 m: __ dB(A) ; heating: loop __ → 43 °C in __ min (bath __ → __ °C)
Safety checks: cutoffs opened at __/__/__ °C (plates), __ °C (heatsink); NO_FLOW after __ s; HOST_TIMEOUT after __ s
```

- **Problems and lessons learned**, **safety checkboxes**, **photos** (wiring, thermal stack, loop, HA graphs).
- Attach the CSV exports.
