# Feature parity: Pod 6 → Open Bed Climate

What a commercial Pod 6 does, according to **public sources** (product pages, launch coverage and open-source
client projects, collected in [`research/prior-art.md`](research/prior-art.md)), and how Open Bed Climate covers it.

Status: ✅ in the design now · 🔜 planned, contributions welcome · 🔌 via existing third-party products · ❌ out of scope

| Pod 6 feature (public) | Open Bed Climate approach | Module | Status |
|---|---|---|---|
| Per-side water temperature control, heating + cooling | TEC (Peltier) thermal module per zone, 13–43 °C setpoint range | Thermal | ✅ |
| Two independent zones; "Solo" single-zone variant | `zones = 1` or `2` in the kit file | Kit config | ✅ |
| 3 TECs per side, ~550 W PSU | 4 standard TEC modules per zone in Duo kits (Pod 6's module size isn't public). Capping each at 4.5 A costs 0.4 K of cooling and saves 44 % power, so each zone runs from one certified 280 W plug-in supply | Thermal, Power | ✅ |
| Compact hub with internal reservoir, fast priming | Small reservoir with level sensor and a pump-only prime cycle (`PRIME`) | Thermal | ✅ |
| One combined connector for water + data | Dry-break water couplings plus one low-voltage data cable, bundled in a sleeve. A truly single connector is a nice-to-have. | Water mat | 🔜 |
| Temperature schedule through the night ("Autopilot", subscription) | User-owned schedule curves with a wake ramp, run on the hub itself with no subscription | Software | ✅ basic, 🔜 adaptive |
| Thermal wake-up alarm | Warm ramp before the wake time | Software | ✅ |
| Vibration alarm | Vibration motor puck under the pillow/cover with a haptic driver | Add-on | 🔜 |
| Multi-point biometric sensing in the cover (Pod 6: "9 sensors per side"; the physical sensor type is not public) | Three interchangeable options: **load cells** under the bed legs, **pneumatic** air tube + pressure sensor, or a **piezo grid** (our own 3×3 layout choice) | Sensing | 🔜 |
| Presence / in-bed detection | Any of the sensing options; also starts the schedule | Sensing | 🔜 |
| Heart rate, HRV, breathing rate | BCG signal processing on the hub (not a medical device) | Sensing, Software | 🔜 |
| Sleep stages, sleep score | Derived from HR/HRV/breathing/movement; open algorithms only | Software | 🔜 |
| Tap gestures on the cover | Piezo-grid option can detect taps; other options can use a bedside button | Sensing | 🔜 |
| Away mode, nap mode, "hot flash" mode (seen in community API clients) | Schedule presets and manual overrides | Software | 🔜 |
| App control | Local web UI plus **Home Assistant** (MQTT discovery or ESPHome) | Software | 🔜 |
| Cloud account, subscription | Not needed: local-only by design | — | ❌ (on purpose) |
| Adjustable base with elevation, anti-snore | Use an existing adjustable base with community Home Assistant integrations; anti-snore triggers it from detected snoring/movement | 🔌 + Software | 🔌 |
| Speaker in the base | Any Home Assistant media player | 🔌 | 🔌 |
| Blanket (water-cooled top layer) | Second water mat on the same thermal module, with a valve or its own zone | Water mat | 🔜 |
| Pillow cover | Small water mat on its own low-power zone | Water mat | 🔜 |
| Over-the-air updates | Hub software and firmware updates you run yourself | Software | 🔜 |

## Where Open Bed Climate deliberately goes further
- **Local-first and private.** No cloud, and biometric data never leaves your home unless you export it.
- **Repairable and adaptable.** Standard parts, documented roles and kit files you can change.
- **Measurable claims.** Each kit's performance claims are checked against the thermal model in CI
  (`software/opod/tests/test_kits.py`).
