# Contributing to Open Bed Climate

Thanks for being here! Open Bed Climate is a community project to build an **open, local-first, repairable** bed
climate system from standard parts. You don't need to be an engineer to help: build reports and part tests
matter as much as code.

## Ways to help (pick one!)

| You are… | You can… |
|---|---|
| **A builder** | Build a kit, then share a **Build report** issue with photos, measurements and what went wrong. Real measurements beat our model. |
| **A parts hunter** | Find a cheaper, better or locally available part for a role in [`hardware/parts.toml`](hardware/parts.toml) and open a **Part substitution** issue or PR. |
| **Electronics / safety** | Review [SAFETY.md](SAFETY.md) and [`docs/design/02-electrical-safety.md`](docs/design/02-electrical-safety.md). Design the Tier 1 boards. |
| **Mechanical / textile** | The water mat is the hardest part. Prototype mats, couplings and enclosures. |
| **Firmware** | Bring up [`firmware/obc-pico2`](firmware/) on real hardware, prove the fan/pump PWM and the OPL firmware-update path on a real Pico 2. |
| **Software / Home Assistant** | Extend the [ESPHome hub](hub/esphome/) (schedules on the hub, sensing options), the Linux hub services, biometrics (BCG) algorithms. |
| **Writer / translator** | Make the docs clearer. Docs are in English; translations are welcome under `docs/i18n/<lang>/`. |

Look for issues labelled `good first issue` and `help wanted`.

## Ground rules

1. **Clean-room.** Open Bed Climate is designed from public information only. Do **not** contribute vendor firmware,
   decompiled code, leaked documents, app credentials or device-rooting instructions for commercial products.
   Linking to public third-party projects is fine.
2. **Safety limits are not negotiable in a PR.** Changes to anything in the "What you must not change" table of
   [SAFETY.md](SAFETY.md) need a separate issue and a review by at least two maintainers. Explain why it is safer.
3. **Claims need evidence.** Performance claims go into kit files (`hardware/kits/*.toml`) where the tests check
   them, or come with measurements (method, instrument, conditions).
4. **Parts by role, not by brand.** Every part entry states the role's requirement first, then examples with a
   source link and a `verified_on` date.

## Development

Using an AI coding agent? Point it at [AGENTS.md](AGENTS.md): repo map, hard rules, generated files, full verification.

```sh
cd software/obc
uv run pytest -q          # thermal model, control/safety, protocol, schedule, kit checks
cd ../../firmware
cargo test                # Rust core replays the Python golden vectors
```

Behaviour changes start in the Python reference: change it, run `uv run python -m obc.golden`, then make
the Rust core pass.

- Python reference code: small, typed, no dependencies outside the standard library (tests use pytest).
- Every behaviour change in `control.py` needs a test. Safety behaviour needs a test that fails without the change.
- Add a kit: copy `hardware/kits/solo-starter.toml`, edit it, and run the tests. They tell you if your claims hold.

## Pull requests
- Keep PRs focused, one topic each. Describe what changed and how you verified it.
- Hardware design files: commit the source files (KiCad, FreeCAD, STEP for exchange) plus a PDF/PNG preview.
- By contributing you agree that your contribution is licensed under the project licenses (Apache-2.0 for
  software and docs, CERN-OHL-S-2.0 for hardware).

## Code of Conduct
This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be kind, be precise, assume good faith.
