# Bed Software (hub)

**Two hub options:**
- **ESP32-S3 + ESPHome (Tier 0 default, implemented):** [`hub/esphome`](../../hub/esphome). It exposes climate
  entities, sensors, problem flags and buttons to Home Assistant. Night programs (the curve below) run on the hub itself: a
  switch per side starts the curve at bedtime, a wake-time entity sets the warm ramp, and the start time survives a
  hub reboot. A manual temperature change ends the program for that side.
- **Linux SBC (planned):** the service layout below. Needed for on-device biometrics with the piezo grid.

The Linux variant runs everything the vendor's cloud and app do, locally:

## Services
| Service | Responsibility |
|---|---|
| `opod-link` | Owns both serial ports, OPL encode/decode, heartbeats, telemetry fan-out. The only process that talks to the MCUs. |
| `opod-core` | Per-side state (on/off, target, schedule, away mode), schedule engine (`opod.schedule`), alarm/wake ramps, fault handling and user acknowledgment. |
| `opod-bio` | Consumes `SENSOR_BLOCK` streams and produces presence, HR, HRV, BR and movement. Writes nightly sessions to SQLite. |
| `opod-api` | Local REST + WebSocket API and a web UI on the LAN. |
| `opod-mqtt` | MQTT with Home Assistant discovery: climate entity per side, sensors (water temp, HR, BR, presence), fault binary sensors. |
| `opod-ota` | Updates for the hub software (A/B or package-based) and MCU firmware. Never auto-updates at night. |

Internal bus: a local MQTT broker (Mosquitto). Each service is a small process; `opod-link` is the safety-relevant
one and stays minimal.

## Schedules ("autopilot" replacement)
- Each side has a user-defined curve: points of (minutes after bedtime, °C) plus a wake ramp
  (`opod.schedule.Schedule`). Default curve: 24 °C at bedtime → 21 °C after 30 min → 20 °C deep-sleep phase →
  23 °C → 25 °C, then a 30 min warm ramp to 32 °C before wake.
- Bedtime is triggered by presence detection (bed occupied for 5 min) or a fixed time, whichever comes first.
- Pre-cool or pre-heat starts 45 min before the expected bedtime (needed for the 13–17 °C range, see thermal doc).
- Adaptive mode (later): adjust the curve points nightly from movement and HR during each phase, with a hard
  limit of ±1 °C per night. Every change is logged and explainable in the UI.

## Alarms
v1 has no vibration motor (open decision). Thermal wake (warm ramp) is supported now. A vibration alarm needs an
ERM motor on the cover sensor board, which is cheap to add.

## Privacy defaults
- No outbound network traffic by default. Biometric data stays on the hub.
- Export is a user action (CSV/JSON).
