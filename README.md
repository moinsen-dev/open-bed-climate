# Open Bed Climate

**An open-source, local-first bed climate system you can build, repair and adapt yourself.**

Open Bed Climate cools and warms each side of your bed with water, tracks presence, heart rate and breathing,
and runs your sleep temperature schedule — like the commercial "smart mattress cover" systems, but:

- 🔓 **Open:** hardware (CERN-OHL-S-2.0) and software (Apache-2.0), designed clean-room from public information
- 🏠 **Local-first:** no cloud, no account, no subscription; native **Home Assistant** integration
- 🔧 **Standard parts:** PC-watercooling components, Peltier modules, Raspberry Pi Pico, ESP32, certified plug-in power supplies
- 🧩 **DIY kits you can adapt:** one zone or two, cheap or high-performance, three sensing options

> ⚠️ **Safety first.** This project combines water, several hundred watts and a sleeping person.
> Read [SAFETY.md](SAFETY.md) before you build anything. Nothing here is certified.

## Status: design phase. Help us build the first prototype!

| Area | State |
|---|---|
| Feature parity analysis | ✅ [docs/FEATURES.md](docs/FEATURES.md) |
| System design, safety concept | ✅ [docs/design/](docs/design/) · [SAFETY.md](SAFETY.md) |
| Kits and parts catalog | ✅ first version: [hardware/](hardware/) |
| Reference software (thermal model, control + safety logic, protocol, schedules) | ✅ tested: [software/opod](software/opod) |
| Control firmware for the Pico 2 (Rust/embassy) | ✅ compiles, matches the reference; 🔜 first hardware bring-up: [firmware/](firmware/) |
| Hub: ESPHome component + Home Assistant entities, night programs on the hub | ✅ compiles for ESP32-S3, protocol and schedule host-tested; 🔜 first hardware run: [hub/esphome/](hub/esphome/) |
| First physical build + measurements | 🔜 **help wanted, the most valuable contribution right now**: follow the [build guide](docs/build/) |

## Pick a kit

| Kit | Zones | Best for | Approx. coldest water* |
|---|---|---|---|
| [Solo Starter](hardware/kits/solo-starter.toml) | 1 | first build, single sleeper, lowest cost | ~21.7 °C |
| [Duo Standard](hardware/kits/duo-standard.toml) | 2 | couples, strongest cooling from standard parts | ~18.8 °C |
| [Duo Reference](hardware/kits/duo-reference.toml) | 2 | experienced builders, custom PCBs, best biometrics | ~18.5 °C |

\* Model estimate, sleeper in bed in a 25 °C room. All kits warm to 43 °C. Kits are plain TOML files: copy one,
change it, and the test suite checks whether your build can deliver what it claims.

## How it works

```
 bed:   [ water mat ] ←─ water lines ─→ ┌──────────────── hub ────────────────┐
        [ sensing   ] ── data cable ──→ │ Peltier thermal module(s), pump      │
                                        │ Pico 2 control MCU (safety limits)   │
                                        │ ESP32/ESPHome hub ⇄ Home Assistant   │
                                        │ certified 24 V + 12 V supplies       │
                                        └──────────────────────────────────────┘
```

Details: [architecture](docs/design/00-architecture.md) · [thermal](docs/design/01-thermal-fluidics.md) ·
[electrical safety](docs/design/02-electrical-safety.md) · [sensing](docs/design/03-sensing-biometrics.md) ·
[protocol](docs/design/04-firmware-protocol.md) · [software](docs/design/05-bed-software.md) ·
[open decisions](docs/design/OPEN-DECISIONS.md)

## Get involved

Builders, parts hunters, electronics and textile people, firmware and Home Assistant developers, writers:
there is a place for you. Start with [CONTRIBUTING.md](CONTRIBUTING.md).

**Build it:** the [build guide for prototype 0](docs/build/) (Solo Starter, bench first, then bed) takes you
step by step from parts to a commissioned unit and the measurements the model still needs.

```sh
cd software/opod && uv run pytest -q    # reference model, safety logic, kit checks
cd firmware && cargo test               # firmware core vs. golden vectors
```

## Background

Commercial systems in this space (e.g. Eight Sleep Pod) are cloud-bound and subscription-based. A community has
already built local replacements for older Pod hardware; see [docs/research/prior-art.md](docs/research/prior-art.md).
Open Bed Climate takes a different route: **our own open hardware**, so nobody depends on a vendor's servers to sleep well.
Open Bed Climate is not affiliated with or endorsed by Eight Sleep.

## License
Software and documentation: [Apache-2.0](LICENSE) · Hardware designs: [CERN-OHL-S-2.0](LICENSE-HARDWARE)
