# STATE — Open Bed Climate (sleep_pod)

> **Frozen:** 2026-10-11
> **Branch:** (git init, no commits yet)
> **Last commit:** none
> **Dirty:** all files untracked

## Last work-unit

The project is a clean-room **open hardware** design with Pod 6 feature parity as the target, standard parts and
customisable DIY kits. English docs written to invite contributors. Licenses decided: Apache-2.0 (software/docs),
CERN-OHL-S-2.0 (hardware).
- Kits are TOML (`hardware/kits/`). `opod.kit` checks every claim against the thermal model.
- The parts catalog `hardware/parts.toml` lists roles first, then examples with status, source and date; `PARTS.md`
  is generated from it.
- Tier 0 power: one 24 V IEC-inlet brick per zone → DPS-class buck (Modbus) → fuse → zone relay → polarity relay → 4 TECs capped at 4.5 A (Duo; Solo 3 TECs at 5 A).
  No mains wiring by builders.
- The TEC model is fitted to the TEC1-12706 datasheet (the earlier guess was ~20 % optimistic). The controller has a flow interlock, a heating taper (end point 48 °C) and a polarity dead time. Kit tests: claims, PSU load in a 30 °C room, heating without tripping the cutoffs. 38 tests green.
- **Firmware (2026-10-10):** `firmware/opod-core` (no_std Rust) replays the Python golden vectors (8 scenarios, including 10 Hz,
  jittered dt and 1-year uptime; max deviation 1e-5 A) and adds a host-tested TEC-driver state machine. `firmware/opod-pico2`
  (embassy, RP2350) compiles: ~50 KB flash. **Not run on hardware.** Wiring: `hardware/WIRING.md`.
- **Hub (2026-10-10):** ESPHome external component `hub/esphome/components/opod` (climate per zone, sensors, problem/link
  binary sensors, prime/clear-faults buttons, Bluetooth proxy for adjustable bases). `opl.h` is host-tested against the
  same golden frames (ASan/UBSan clean). The example config compiles for ESP32-S3 with ESPHome 2026.9.1 (RAM 40 %, flash 64 %; protocol headers in namespace `openpod`). Not run on hardware.
- **Night programs on the hub (2026-10-11):** `schedule.h` (C++ port of `opod.schedule`, 731 Python-generated vectors in
  `test/schedule.txt`, checked for freshness by pytest) + `switch` platform `opod`: per-side switch, curve points in YAML,
  wake-time entity, start time persisted in flash, a manual change ends the program. Compiles (RAM 40 %, flash 65 %).
- **Name (2026-10-11):** renamed to **Open Bed Climate** (trademark risk: Eight Sleep holds POD® and opposes "…POD" marks).
  Docs renamed; protocol is now "Open Peltier Link" (OPL). Code identifiers (`opod`, ESPHome `platform: opod`) not yet renamed.
- **Parts verified (2026-10-11):** GST280A24 (datasheet), GST90A12 = 80 W → Solo only; Duo Standard aux = 120 W (GST120A12, unverified);
  CIT A102 DPDT relay; Sensata 67L050/67L080 cutoffs (listing, no UL found); leak sensors with fault output. DPS5020 live registers
  match `modbus.rs`; function codes / current scaling to confirm on the unit.
- **Website (2026-10-11):** Astro 7 static site in `website/` (30 pages, "Thermal Night" design per `DESIGN.md`, hero plays the real night curve,
  kit picker, schedule editor → hub YAML). `npm run verify` green (astro check, tests vs repo data, budgets, CSP/no-third-party guard, links).
  Model numbers come from `python -m opod.site_data` (freshness-tested). Placeholders in `website/src/site.ts`. Not deployed.
  Funding: NLnet call deadline **2026-11-03** (write the proposal yourself, GenAI policy); Prototype Fund (software only) until 2026-11-30.

## Next intended step

1. Website go-live; owner decisions: domain, GitHub org/repo URL, contact address, Impressum, sponsor channel.
2. Rename code identifiers `opod` → new name (package, crates, ESPHome platform) in one sweep.
3. Fan/pump PWM in the firmware; OPL firmware-update path.

## Open friction

- No physical prototype; all thermal numbers are model estimates. DPS5020 ripple, register map and EEPROM behaviour are unverified.
- Dew-point guard is implemented in the ESPHome hub, but only active when room sensors are configured (commented out in the example).
- Repo not yet published (no remote); the CODE_OF_CONDUCT contact address is a placeholder.
