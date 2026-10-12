# AGENTS.md

Instructions for AI coding agents (Claude Code, Codex, Copilot, Cursor, …) working in this repository.
Human contributors: start with [CONTRIBUTING.md](CONTRIBUTING.md). Everything here applies to you too.

## What this is

Open Bed Climate is an open-source, local-first bed cooling/heating system. A water mat is cooled or warmed by
Peltier (TEC) modules. A Raspberry Pi Pico 2 runs the safety-critical control loop, and an ESP32-S3 running
ESPHome is the hub to Home Assistant. Hardware is CERN-OHL-S-2.0; software and docs are Apache-2.0.
**Nothing has been built or measured yet:** every performance number is a model estimate.

## Hard rules

1. **Clean-room.** Use public information only. Never add vendor firmware, decompiled or disassembled code,
   leaked documents, app credentials or rooting steps for commercial products (e.g. Eight Sleep Pod). Don't use
   the "Pod" name or marks for this project.
2. **Safety limits are fixed.** Do not change the limits in the "What you must not change" table of
   [SAFETY.md](SAFETY.md): max setpoint 43 °C, the 45 °C / 75 °C trips, the flow interlock, polarity dead time,
   leak and heartbeat handling, or "TEC enable defaults to off". If a task seems to need such a change, stop and
   ask. Never weaken a safety test to make it pass.
3. **No unverifiable claims.** Performance claims go into `hardware/kits/*.toml`, where the tests check them
   against the thermal model, or come with a real measurement. Mark untested hardware and firmware paths as
   untested in the docs.
4. **No third-party requests on the website.** Strict CSP: no CDNs, analytics, fonts from other hosts, iframes
   or inline scripts/styles. `npm run guard` enforces this.
5. **English only** in code, docs, commit messages and the website.

## Repository map

| Path | What | Language |
|---|---|---|
| `software/obc/` | **Reference implementation** (thermal model, controller, safety logic, OPL protocol, night schedules, fan/pump cooling, firmware-update session, kit checks). The source of truth for behaviour. | Python ≥ 3.11, stdlib only |
| `firmware/obc-core/` | `no_std` Rust port of the reference; replays the Python golden vectors | Rust |
| `firmware/obc-pico2/` | Embassy app for the RP2350 (Pico 2). Kit features: `kit-solo-starter`, `kit-duo-standard` (default), `kit-duo-reference`. Pin map in `src/board.rs`. | Rust |
| `hub/esphome/` | ESPHome external component `obc` (`components/obc/`), configs `obc-hub*.yaml`. Protocol headers `opl.h`, `schedule.h`, `opl_fw.h` have no ESPHome dependency (namespace `::openbed`). | C++17 / YAML |
| `hub/ha-card/` | Home Assistant dashboard card | TypeScript, Lit, Vite |
| `hardware/` | `parts.toml` (parts by role), `kits/*.toml`, `shopping/*.toml`, `WIRING.md`, `pcb/carrier/` (KiCad, generated from `scripts/design.py`) | TOML / KiCad |
| `docs/` | Design docs (`design/`), build guide (`build/`), research (`research/`) | Markdown |
| `website/` | Astro static site, https://openbedclimate.moinsen.dev. Design rules in [DESIGN.md](DESIGN.md). | Astro / TS / CSS |

The protocol between Pico and hub is **OPL** (Open Peltier Link): COBS framing, CRC-16/CCITT-FALSE, documented
in `docs/design/04-firmware-protocol.md`.

## Behaviour changes: Python first

Python, Rust and C++ must agree byte-for-byte or to within float tolerance. The workflow:

1. Change the Python reference in `software/obc/src/obc/` and add or extend tests.
2. Regenerate the vectors with `cd software/obc && uv run python -m obc.golden`. This writes
   `firmware/obc-core/tests/vectors/golden.json` and the hub's `test/frames.txt` and `test/schedule.txt`.
3. Make the Rust core (`cargo test`) and the C++ host tests pass against the new vectors.

pytest fails if any generated file is stale.

## Generated files: never edit by hand

| File | Edit instead | Regenerate (in `software/obc`) |
|---|---|---|
| `hardware/PARTS.md` | `hardware/parts.toml` | `uv run python -m obc.render_parts` |
| `hardware/shopping/*.md` | `hardware/shopping/*.toml` | `uv run python -m obc.shopping` |
| `website/src/data/model.json` | Python model / kit TOMLs | `uv run python -m obc.site_data` |
| golden vectors, `frames.txt`, `schedule.txt` | Python reference | `uv run python -m obc.golden` |
| `hardware/pcb/carrier/*.kicad_*`, `fab/` | `hardware/pcb/carrier/scripts/design.py` | `./build.sh` (KiCad 10 + Freerouting 1.9.0, see its header) |

The carrier PCB pin map is tested against `firmware/obc-pico2/src/board.rs`. If you change pins, change both
together.

## Verify before you call it done

Run what your change touches. CI (`.github/workflows/test.yml`) runs all of it on every push.

```sh
cd software/obc && uv run pytest -q                       # reference, kit checks, freshness of generated files
cd firmware && cargo test                                 # Rust core vs. golden vectors
cd firmware/obc-pico2 && for k in solo-starter duo-standard duo-reference; do \
  cargo build --release --locked --no-default-features --features kit-$k; done
cd hub/esphome/components/obc/test && \
  c++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -I.. test_opl.cpp -o test_opl && ./test_opl frames.txt && \
  c++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -I.. test_schedule.cpp -o test_schedule && ./test_schedule schedule.txt
cd hub/esphome && uvx --from esphome==2026.9.1 esphome compile obc-hub.yaml   # needs a throwaway secrets.yaml, see CI
cd hub/ha-card && npm ci && npm test && npm run build
cd website && npm ci && npm run verify                    # astro check, tests, build, budgets, CSP guard, links
```

Notes:
- `website` prebuild downloads the latest release's firmware into `public/firmware/` (git-ignored).
- The site's CSS budget is nearly full (about 19 of 20 KB gzip): reuse existing classes and tokens.
- Internal website links need a trailing slash.
- Pico 2 pull-downs must be ≤ 8.2 kΩ (RP2350-E9); the docs use 4.7 kΩ.

## Conventions

- **Python:** small, typed, standard library only (pytest for tests). Every behaviour change in `control.py` has
  a test; safety behaviour has a test that fails without the change.
- **Rust:** `obc-core` stays `no_std`, without allocation. Keep `Cargo.lock` consistent: CI builds with `--locked`.
- **Parts:** by role, not by brand. Give the requirement first, then examples with a source link and a
  `verified_on` date. Mark unverified data as unverified.
- **Docs:** plain, precise English. Link to files instead of duplicating numbers that a generator owns.
- **Commits:** one topic each; say what changed and how it was verified. Don't commit secrets
  (`hub/esphome/secrets.yaml` and `*.local.yaml` are ignored).
- **Releases:** tags `v*` trigger `.github/workflows/release.yml` (UF2 per kit, hub factory image, HA card,
  SHA256SUMS). Raise the `obc-pico2` crate version with each release. Release builds don't enable the `tbyb`
  feature until the OPL update path has been proven on hardware.

## Where things stand

[STATE.md](STATE.md) holds the current state and next steps. [docs/design/OPEN-DECISIONS.md](docs/design/OPEN-DECISIONS.md)
lists open decisions and needed measurements. Open work is tracked in GitHub issues.
