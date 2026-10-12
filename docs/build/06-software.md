# Step 6: Software

**Goal:** the Pico 2 runs the **Solo Starter** control firmware, the ESP32-S3 runs the hub, and Home Assistant shows
the hub's entities.

**Time:** 1–2 h.

> ⚠️ The firmware **has not run on real hardware yet** (`firmware/README.md`). Treat the first boot as a test, with
> the 24 V brick unplugged.

## 6.1 Control firmware (Pico 2)

The firmware is built **per kit**. The kit sets the TEC current limit: Solo Starter = 3 TECs × 5.0 A = **15 A** zone
current, and zone 1 inert. **Flash only the `solo-starter` image**; another kit's image can exceed your parts' rating.

### Option A: download the UF2 (no toolchain)

1. Open the latest release at <https://github.com/moinsen-dev/open-bed-climate/releases> and download
   **`obc-pico2-solo-starter.uf2`** and `SHA256SUMS`.
2. Check the file: `sha256sum -c SHA256SUMS --ignore-missing` (Linux) or `shasum -a 256 obc-pico2-solo-starter.uf2`
   (macOS) and compare with the line in `SHA256SUMS`.
3. Unplug the 24 V brick. Hold the Pico's **BOOTSEL** button, plug in USB, release. A USB drive appears (named
   `RP2350` on a Pico 2).
4. Drag `obc-pico2-solo-starter.uf2` onto the drive. The Pico reboots into the firmware and the drive disappears.

Prebuilt images use the **generic NTC values** (10 kΩ, β 3435) and a flow factor of **98 Hz per L/min**, which fits
YF-S401-class turbine sensors. Use option B if your NTC calibration in [step 2](02-control-board.md#ntc-calibration)
was more than 1 °C off the generic model, or if your flow sensor needs a different factor. You check the factor in
[step 7, section 2.2](07-bench-commissioning.md#22-calibrate-the-flow-reading-fuse-still-pulled) before any TEC gets
power. The shopping list's YF-S401 matches the prebuilt factor; other flow sensors almost certainly need option B.

### Option B: build from source

Needed for your own NTC calibration, your flow factor, or a temporary low current limit for bench tests.

```sh
rustup target add thumbv8m.main-none-eabihf
cd firmware
cargo test                                    # core logic vs. golden vectors, no hardware needed
cd obc-pico2
# edit src/board.rs: NTC_CAL (your r25/beta), FLOW_HZ_PER_LPM (your sensor)
cargo build --release --no-default-features --features kit-solo-starter
```

Flash it:

- **With a debug probe** (a second Pico running `debugprobe`, wired to the SWD pins):
  `cargo run --release --no-default-features --features kit-solo-starter`. This also streams the `defmt` log.
- **Without a probe:** hold BOOTSEL, plug in, then
  `picotool load -u -v -x -t elf target/thumbv8m.main-none-eabihf/release/obc-pico2`.

What you may change in `board.rs`: calibration (`NTC_CAL`, `FLOW_HZ_PER_LPM`), the register map after verifying it
(`DPS_MAP`), and, for a bench test only, `MAX_TEC_CURRENT_A` in the `kit-solo-starter` block (**down** only; the core
clamps it to 6 A). Revert that one afterwards and never commit it: it must match `hardware/kits/solo-starter.toml`, and
the kit tests check that.
What you must not change: the safety limits in `obc-core::control` (43 °C, 45 °C, 75 °C, flow interlock, heartbeat,
dead time). See [SAFETY.md](../../SAFETY.md).

### ✅ Checkpoint: first boot (24 V brick unplugged)

- [ ] With a probe: the log shows a start line with **`solo-starter`**, **1 active zone**, **5 A × 3 TECs**.
- [ ] Without a probe: there is no visible sign yet (no status LED). Check that every output gate (GP10–GP13) still
      reads **< 0.3 V** and nothing clicks. The hub link in 6.3 is your real checkpoint.

## 6.2 Hub (ESP32-S3)

### Option A: browser installer

1. Open <https://openbedclimate.moinsen.dev/install/> in **Chrome or Edge** (Web Serial is needed).
2. Connect the ESP32-S3 by USB (disconnect its 5 V pin from the control board's rail while USB is plugged in, unless
   your board protects against back-feed). Click install, choose the port, wait.
3. Set Wi-Fi right after flashing in the browser (Improv over USB). Alternatives: Improv over Bluetooth, or the
   `open-bed-climate-xxxxxx` access point and its captive portal.

The installer flashes the same image as `obc-hub-factory.bin` in the release, so you can also flash it with
`esptool.py write_flash 0x0 obc-hub-factory.bin`.

### Option B: ESPHome CLI

```sh
cd hub/esphome
cp secrets.example.yaml secrets.yaml   # Wi-Fi, api_key (openssl rand -base64 32), ota_password
esphome run obc-hub.yaml              # or: uvx --from esphome esphome run obc-hub.yaml
```

The device (pins, entities, night programs) is defined in `obc-hub-common.yaml`. For a Solo build you can delete the
`right` / zone 1 entries there; with the Solo firmware they are harmless either way.

### Room sensor (strongly recommended before stage B)

Add an SHT45 (role `temp_sensors`) on the hub's I2C bus and set `room_temperature` / `room_humidity` in the `obc:`
block. That enables the **dew-point guard** (cooling setpoints below 16 °C are raised to at least dew point + 1 K) and
gives you the room temperature for the measurements in step 7. See `hub/esphome/README.md`.

## 6.3 Adopt in Home Assistant

1. Home Assistant → Settings → Devices & services. The hub appears as a discovered **ESPHome** device. Click
   **Configure**. (Factory image: Home Assistant sets the API encryption key itself when it adopts the device. CLI
   build: enter the `api_key` from your `secrets.yaml`.)
2. Open the device page. You get, per side: a **climate** entity (off / heat_cool, 13–43 °C), water and heatsink
   temperature, TEC current, flow and fault code sensors, a **problem** binary sensor and a **clear faults** button; plus
   **Control board link** and **Prime water loop**.
3. Hide or disable the **Right** entities: on a Solo build they always show no temperature and reject any target.

Sensor notes:

- **TEC current is per TEC.** Home Assistant shows 5.0 A when the DPS shows 15 A (3 × 5 A).
- The example config averages the diagnostic sensors over **30 s** (`throttle_average`). That is fine for the
  measurements in step 7; shorten it in `obc-hub-common.yaml` if you need faster curves.

### Fault code

The fault code sensor is a bit field (`04-firmware-protocol.md`). Add up the values:

| Value | Fault | Latching (needs **clear faults**) |
|---|---|---|
| 1 | water over-temperature (> 45 °C) | yes |
| 2 | water under-temperature (< 8 °C) | no |
| 4 | hot side over-temperature (> 75 °C) | yes |
| 8 | no flow (< 0.15 L/min for 20 s while enabled) | no |
| 16 | leak | yes |
| 32 | sensor invalid (NTC open/short) | yes |
| 64 | host timeout (no heartbeat for 10 s while enabled) | no |
| 128 | low water | no |
| 256 | TEC driver communication (3 failed Modbus transactions) | firmware-only |

Example: 160 = 128 + 32 = low water and an invalid sensor.

## ✅ Checkpoint (hub and control board connected, 24 V brick still unplugged, loop filled)

- [ ] **Control board link: on** within a few seconds of power-up.
- [ ] Left water temperature ≈ your bath reference thermometer (± 1 °C, more if uncalibrated). Left heatsink
      temperature ≈ room temperature.
- [ ] Left flow: **0** (pump off, climate off).
- [ ] Left fault code: **256** (TEC driver communication). That is correct here: the DPS gets its power from the
      unplugged 24 V brick, so the firmware's Modbus writes fail. Any other bit set means a sensor, leak or level problem
      to fix first. In step 7, with the DPS powered and talking, it drops to **0**.
- [ ] Unplug the hub's UART wires: within **5 s** "Control board link" goes **off** and "Left problem" goes **on**.
      Plug back in: link on again.
- [ ] Press **Prime water loop**: the pump runs for **60 s**, flow shows **≥ 0.15 L/min**, then the pump stops.

## If it fails

- **No USB drive in BOOTSEL mode:** charge-only USB cable, or BOOTSEL released too early.
- **Link stays off:** TX/RX not crossed (ESP32 GPIO17 → Pico GP1, GPIO18 ← GP0), missing GND between the boards, or the
  Pico not running (re-flash).
- **Water temperature unavailable / fault 32:** NTC divider or ADS1115 wiring (check the node voltage, I2C address
  0x48, SDA/SCL swapped).
- **Fault 16 right away:** leak input HIGH: sensor module unpowered, wrong contact, or a real leak.
- **Fault 128 right away:** level input HIGH: reservoir below the sensor, sensor polarity, or a broken wire.
- **Prime does nothing:** prime only runs while there is no leak and the level is OK; check the fault code.
