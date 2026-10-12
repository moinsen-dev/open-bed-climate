# STATE — Open Bed Climate (sleep_pod)

> **Frozen:** 2026-10-11
> **Branch:** main → github.com/moinsen-dev/open-bed-climate (public)
> **Last commit:** see git log
> **Dirty:** clean after this commit

## Last work-unit

The project is a clean-room **open hardware** design with Pod 6 feature parity as the target, standard parts and
customisable DIY kits. English docs written to invite contributors. Licenses decided: Apache-2.0 (software/docs),
CERN-OHL-S-2.0 (hardware).
- Kits are TOML (`hardware/kits/`). `obc.kit` checks every claim against the thermal model.
- The parts catalog `hardware/parts.toml` lists roles first, then examples with status, source and date; `PARTS.md`
  is generated from it.
- Tier 0 power: one 24 V IEC-inlet brick per zone → DPS-class buck (Modbus) → fuse → zone relay → polarity relay → 4 TECs capped at 4.5 A (Duo; Solo 3 TECs at 5 A).
  No mains wiring by builders.
- The TEC model is fitted to the TEC1-12706 datasheet (the earlier guess was ~20 % optimistic). The controller has a flow interlock, a heating taper (end point 48 °C) and a polarity dead time. Kit tests: claims, PSU load in a 30 °C room, heating without tripping the cutoffs. 38 tests green.
- **Firmware (2026-10-10):** `firmware/obc-core` (no_std Rust) replays the Python golden vectors (8 scenarios, including 10 Hz,
  jittered dt and 1-year uptime; max deviation 1e-5 A) and adds a host-tested TEC-driver state machine. `firmware/obc-pico2`
  (embassy, RP2350) compiles: ~50 KB flash. **Not run on hardware.** Wiring: `hardware/WIRING.md`.
- **Hub (2026-10-10):** ESPHome external component `hub/esphome/components/obc` (climate per zone, sensors, problem/link
  binary sensors, prime/clear-faults buttons, Bluetooth proxy for adjustable bases). `opl.h` is host-tested against the
  same golden frames (ASan/UBSan clean). The example config compiles for ESP32-S3 with ESPHome 2026.9.1 (RAM 40 %, flash 64 %; protocol headers in namespace `openbed`). Not run on hardware.
- **Night programs on the hub (2026-10-11):** `schedule.h` (C++ port of `obc.schedule`, 731 Python-generated vectors in
  `test/schedule.txt`, checked for freshness by pytest) + `switch` platform `obc`: per-side switch, curve points in YAML,
  wake-time entity, start time persisted in flash, a manual change ends the program. Compiles (RAM 40 %, flash 65 %).
- **Name (2026-10-11):** renamed to **Open Bed Climate** (trademark risk: Eight Sleep holds POD® and opposes "…POD" marks).
  Docs renamed; protocol is now "Open Peltier Link" (OPL). Code identifiers renamed `opod` → `obc` on 2026-10-12 (package, crates, ESPHome platform; C++ namespace `openbed`).
- **Parts verified (2026-10-11):** GST280A24 (datasheet), GST90A12 = 80 W → Solo only; Duo Standard aux = 120 W (GST120A12, unverified);
  CIT A102 DPDT relay; Sensata 67L050/67L080 cutoffs (listing, no UL found); leak sensors with fault output. DPS5020 live registers
  match `modbus.rs`; function codes / current scaling to confirm on the unit.
- **Website (2026-10-11):** Astro 7 static site in `website/` (30 pages, "Thermal Night" design per `DESIGN.md`, hero plays the real night curve,
  kit picker, schedule editor → hub YAML). `npm run verify` green (astro check, tests vs repo data, budgets, CSP/no-third-party guard, links).
  Model numbers come from `python -m obc.site_data` (freshness-tested). Live: https://openbedclimate.moinsen.dev (CF Pages project `open-bed-climate`; deploy: `cd website && npm run build &&
  CLOUDFLARE_ACCOUNT_ID=331bab3c877a2ace8753d42d9aa33660 wrangler pages deploy dist --project-name=open-bed-climate --branch=main`).
  Impressum/privacy → moinsen.dev, contact business@moinsen.dev, sponsors by e-mail. CSP blocks the zone's CF analytics beacon (intended).
  Funding: NLnet call deadline **2026-11-03** (write the proposal yourself, GenAI policy); Prototype Fund (software only) until 2026-11-30.

- **Prototype 0 kit (2026-10-11):** Solo Starter shopping list `hardware/shopping/solo-starter.toml` (→ .md + /kits/solo-starter/shopping/,
  bench ~€1,084 + bed ~€262, 48 estimate lines), build guide `docs/build/` (bench stage with 10 L bath, 8 steps, SVGs, → /build/),
  per-kit Pico 2 UF2 releases (`release.yml`, picotool 2.3.1, `check_uf2.py`), ESPHome factory image + browser installer (/install/).
  Doc fixes: pull-downs 4.7 kΩ (E9), fuse after DPS, one 80 °C cutoff per heatsink. Open: DPS5020 comm pinout/current scaling.
- **HA dashboard card (2026-10-11):** `hub/ha-card/` (Lit, single JS, 26 tests incl. curve vectors), release asset from v0.1.1.
- **Carrier PCB Rev A (2026-10-11):** `hardware/pcb/carrier/` generated from `scripts/design.py` (`build.sh`, KiCad 10.0.6 in ~/Applications + Freerouting).
  100×100 mm, 2 layers, ERC 0 / DRC 0 (15 silk warnings), JLC BOM/CPL + Gerbers in `fab/`, ~€20–27/board at 10 pcs. Pin map tested against board.rs.
  UNTESTED: LCSC numbers for P-FET/SS54/zener/inductor/electrolytics/0.1 % resistors, rotations, ESP32 row pitch, buck layout, 12 V copper (2 oz for Duo).
- **Water mat sourcing (2026-10-11):** `docs/research/water-mat-sourcing-2026-10.md` + RFQ template. ~€250–600/mat at 10 pcs, tooling €0.8–9k; tiled 45×100 cm design as mitigation.

## Next intended step

1. First hardware: bench build of the Solo Starter (owner orders parts).
2. Seed 10–15 good-first-issues + Discussions categories; NLnet proposal (owner writes it, deadline 2026-11-03).
3. Fan/pump PWM in the firmware; OPL firmware-update path.

## Open friction

- No physical prototype; all thermal numbers are model estimates. DPS5020 ripple, register map and EEPROM behaviour are unverified.
- Dew-point guard is implemented in the ESPHome hub, but only active when room sensors are configured (commented out in the example).
