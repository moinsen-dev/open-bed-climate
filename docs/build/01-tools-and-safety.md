# Step 1: Tools and safety

**Goal:** a safe workspace, the right tools, and a clear picture of what can go wrong before you touch a part.

**Time:** about 1 h.

## Tools

| Tool | Used for | Notes |
|---|---|---|
| Soldering iron (temperature-controlled) + solder + flux | control board, wire joints | |
| **Multimeter** with continuity beep and a 10 A range | every checkpoint | a second meter helps: one on volts, one on amps |
| Wire stripper, side cutters, **crimp tool** for blade/ring/ferrule terminals | power path | crimp, don't just solder, anything that carries TEC current |
| Small screwdrivers, hex keys | relay terminals, heatsink clamps | |
| Hot-air gun (or a hair dryer that gets hot enough) | cutoff test (> 50 °C on a cold plate) | |
| Contact or probe thermometer (thermocouple) | cutoff test, NTC calibration, bath reference | independent of the build's own sensors |
| Kitchen scale | measuring the bath water mass | |
| Optional: waterproof DS18B20 probe on the hub | logs the bench bath temperature in Home Assistant | or read your reference thermometer by hand |
| Measuring jug (1 L) + stopwatch | flow-rate check | |
| **Plug-in mains power meter** | PSU input power | the only thing you plug between the wall and the bricks |
| Paper towels | leak test | lots |
| Zip ties, insulating tape, heat-shrink | | |
| Optional: debug probe (a second Pico running `debugprobe`) | firmware log over SWD | without it you rely on the hub telemetry |
| Optional: signal generator or a spare microcontroller | simulated flow pulses in [step 7](07-bench-commissioning.md) | a spare Pico/Arduino with a 10-line blink sketch works |

## Workspace

1. A table you can get wet: tile floor, or the whole bench setup inside a **large plastic tray** (a storage-box lid or
   shower tray) that holds the whole loop volume with margin (the loop holds ~1–2 L; a tray of ≥ 5 L is plenty).
2. Electronics **above** the water level and away from the plumbing. Plan the layout now: the wet side
   (reservoir, pump, cold plates, bath) and the dry side (PSUs, DPS, relays, control board) with the drip tray
   under the wet side.
3. One mains power strip **with a switch** within reach. This is your emergency stop: it removes power from both
   bricks at once.
4. A smoke detector in the room, and a CO₂ or powder fire extinguisher for electrical fires nearby.

## What can go wrong

| Hazard | How it happens | What protects you | You verify it in |
|---|---|---|---|
| Burn (stage B) | water too hot for prolonged skin contact | 43 °C setpoint cap, 45 °C trip, 50 °C bimetal on each cold plate | step 7 |
| Fire / overheating | TEC hot side not cooled (fan stopped, heatsink loose), overcurrent | 75 °C firmware trip, 80 °C bimetal per heatsink, 20 A fuse, PSU overcurrent protection | step 7 |
| Flooding | loose fitting, cracked tube, coupling that doesn't seal | leak sensor → TECs and pump off; drip tray; 24 h leak test | step 5 |
| Pump stall / air lock | dry pump, kinked tube | flow interlock (no TEC current below 0.15 L/min, `NO_FLOW` after 20 s), level sensor | step 7 |
| Runaway driver | DPS misprogrammed or failed: up to ~21 V on TECs rated 14.4 V | zone relay (opens on any cutoff), fuse, PSU OCP | step 3, step 7 |
| Hub crash | Wi-Fi/ESP32 hangs | control board goes safe 10 s after the last heartbeat | step 7 |
| Control board crash | firmware bug, brown-out | 1 s hardware watchdog; external 4.7 kΩ pull-downs (≤ 8.2 kΩ, erratum E9) keep every output off | step 2, step 7 |
| Condensation | water below room dew point | insulation, drip tray, dew-point guard on the hub | step 4, step 8 |

## Rules for the whole build

- ⚠️ Unplug **both** bricks before you change any wiring. The DPS keeps its input capacitors charged for a few
  seconds; wait, then measure 0 V before you touch the TEC path.
- ⚠️ Never power a TEC without its heatsink and without water flowing on its cold plate. A bare TEC destroys itself in
  seconds and can reach temperatures that burn skin.
- ⚠️ Never bypass a thermal cutoff with a jumper "just for a test". If one is in the way, the test is wrong.
- Keep a **build log**: date, what you did, what you measured. Photos of every wiring stage. The log is the raw
  material for your build report, and it is how other people learn from your build.

## ✅ Checkpoint

- [ ] I have read [SAFETY.md](../../SAFETY.md) and know which limits I must not change.
- [ ] The wet side stands in a tray that holds ≥ 5 L, and the dry side sits above it.
- [ ] A switched power strip is my emergency stop.
- [ ] Multimeter works (continuity beep tested, 10 A range fuse intact).
