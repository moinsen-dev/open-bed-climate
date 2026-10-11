# Safety

Open Bed Climate puts **water, several hundred watts and a sleeping person** in one place. We want people to build
and adapt it, so this page defines clearly what is yours to customise and what is not.

> ⚠️ **Experimental hardware.** Nothing here is certified. You build and use it at your own risk.
> Have the electrical part reviewed by a qualified person before you sleep on a build.
> Never leave a new build running unattended until it has passed the commissioning checklist below.

## What you can customise
- Number of zones, TEC count per zone, heatsinks, pumps and enclosure (describe it in a kit file, and the tests check its claims)
- Sensing option (none / load cells / pneumatic / piezo grid)
- Schedules, presets, UI, Home Assistant automations
- Which hub you use (ESPHome device or Linux single-board computer)

## What you must not change
These limits protect against burns, flooding and fire. They are **not** in any config file. They are compiled
constants in the control firmware (`software/opod/src/opod/control.py` is the reference), backed by hardware that
works even if all software fails.

| Limit | Value | Software | Independent hardware backstop |
|---|---|---|---|
| Max setpoint | 43 °C | clamped in firmware | 50 °C bimetal cutoff on every cold plate |
| Water over-temperature trip | 45 °C, latching | firmware | same cutoffs |
| TEC hot side over-temperature | 75 °C, latching | firmware | 80 °C bimetal on each heatsink |
| Flow interlock | no TEC current until flow ≥ 0.15 L/min; fault after 20 s | firmware | — |
| Polarity switching | the heat/cool relay only switches at zero current, with a 2 s dead time | firmware | relay rated for DC load |
| Leak | TECs and pump off | firmware | drip tray; electronics above the water line |
| Host/network crash | safe state after 10 s without heartbeat | firmware | — |
| Controller crash | — | — | watchdog + pull-down: TEC enable defaults to **off** |

**Architecture rule:** the networked part (ESPHome, Wi-Fi, Linux, Home Assistant) is never the safety part.
Temperature control and limits run on a **separate small control MCU** (Raspberry Pi Pico 2 class) running
Open Bed Climate firmware. The hub can only *request* setpoints over [OPL](docs/design/04-firmware-protocol.md).
Hardware cutoffs switch **relay coils and enable lines**, never the 20 A load current directly.

## Mains
- **Tier 0 kits:** only certified desktop power supplies with an **IEC inlet or molded mains cable**
  (one 24 V supply per zone for the TECs, one 12 V supply for pumps and electronics). You plug them in; you never
  wire mains screw terminals.
- **Tier 1:** a single large supply sits in a **pre-assembled, closed power module** (IEC inlet, fuse, switch).
  Its mains side must be assembled and tested by a qualified electrician. Builders don't open it.
- No mains voltage outside the hub. The cover and bed side carry only water and ≤ 12 V.

## Commissioning checklist (before the first night)
1. Leak test: fill, prime, and run 24 h with the electronics unpowered (pump only, on a separate supply). Check
   every coupling with paper towels.
2. Cutoff test: heat each cold plate with a hot-air gun and confirm the zone relay drops at about 50 °C.
3. Flow interlock: pinch the tube. TEC current must stay at 0 and a `NO_FLOW` fault must appear.
4. Heartbeat: unplug the hub. The control board must go to the safe state within 10 s.
5. Run one full warm cycle to 43 °C and one full cool cycle on an empty bed while you are awake and nearby.

## Reporting a safety issue
Open an issue with the **Safety concern** template. If it could hurt someone who already has a build, say so in
the title. We treat these with top priority.
