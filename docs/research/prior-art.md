# Prior art: Eight Sleep Pod reverse engineering (as of 2026-10-10)

Method: web + GitHub API/raw files read on 2026-10-10. Every claim has a URL. Items marked **[INFERRED]** are my inference, **[UNVERIFIED]** could not be confirmed from a primary source.

## 0. Headline findings

- Pod 6 exists. It launched 2026-09-22/23. Official page: https://www.eightsleep.com/blog/discover-everything-new-with-pod-6
- No public jailbreak, root method or protocol dump exists for Pod 6 yet. free-sleep issue "Pod 6 support?" opened 2026-09-30, 0 comments, still open: https://github.com/throwaway31265/free-sleep/issues/56
- Pod 6 FCC ID is **2AYXT61100005** (grantee 2AYXT, filed 2026-08-21): https://fccid.io/2AYXT61100005. Internal photos, schematics and block diagram are confidential. The exhibit list shows the internal photos and manual with an availability date of 2027-02-17, and schematics and block diagram with no date.
- Pod 6 hardware is a redesign, not a refresh: water tank removed, 3 TECs per side, 550 W PSU, 9 cover sensors per side (vs 1 on Pod 5), water cord and USB merged into one connector. Details in section 2. So the Pod 3/4/5 serial-protocol knowledge may not carry over.

## 1. Existing open replacements / jailbreaks / integrations

### 1.1 Comparison table

| Project | Pod gens | Approach | License | Activity (GitHub API) | URL |
|---|---|---|---|---|---|
| **free-sleep** (throwaway31265) | Pod 3 (SD and no-SD), 4, 5. Pod 1/2 not compatible. Pod 6 not mentioned. | Local jailbreak. Hardware jailbreak via the debug serial port (see their INSTALLATION.md), then install Node/Express + React server and Python biometrics on the Pod. Talks to the stock `frankenfirmware` via the `dac.sock` unix socket (it replaces the DAC). Blocks the 8slp.net hosts. | LICENSE.md is a custom "Open Source Disclaimer" that states MIT. GitHub reports NOASSERTION. | 898 stars, 104 forks, pushed 2026-10-05, 4 open issues | https://github.com/throwaway31265/free-sleep , https://github.com/throwaway31265/free-sleep/blob/main/INSTALLATION.md , https://raw.githubusercontent.com/throwaway31265/free-sleep/main/LICENSE.md |
| **opensleep** (LiamSnow) | Pod 3 tested only. Pod 4/5 "untested". Pod 1/2 not possible. | Needs root via hardware mod. **Replaces all Eight programs** (DAC, Frank, Capybara) in Rust and talks straight to the two STM32 MCUs over USART. MQTT + RON config + Home Assistant. | GPL-3.0 | 157 stars, last push 2026-03-28. Open: #11 Pod 4 investigation, #12 newer Pod 3 "G0" sensor board, #3 Pod 5 request. | https://github.com/LiamSnow/opensleep , https://github.com/LiamSnow/opensleep/issues/11 , https://github.com/LiamSnow/opensleep/issues/12 |
| **lunaris** (Schluggi) | Pod 4 focus. Pod 3/5 "best effort, untested". | AI-assisted fork of opensleep. Same Rust USART approach, MQTT discovery for Home Assistant. Needs root via the free-sleep guide (steps 1-12), then `systemctl disable --now frank`. | GPL-3.0 | 33 stars, created 2026-05-03, pushed 2026-09-24. Biometrics "work in progress". | https://github.com/Schluggi/lunaris |
| **ninesleep** (bobobo1618) | Pod 3 only | Rust. Replaces `dac` only and exposes an HTTP API on :8000 to frankenfirmware. Root via a modified `rootfs.tar.gz` on the SD card. | MIT | 338 stars, last push 2024-05-16 (dormant) | https://github.com/bobobo1618/ninesleep |
| **nightstand** (LTimothy) | Pod 3-5 | Fork of free-sleep, "local-first control". Its Pod 5 capSense2 mapping is referenced by free-sleep. | NOASSERTION | 5 stars, pushed 2026-10-09 | https://github.com/LTimothy/nightstand |
| **EightSleepPod2Server** (a-chaudhari) | Pod 2 | Go implementation of the Spark Protocol server, to talk to a Pod 2 | none stated | 3 stars, pushed 2026-02-16 | https://github.com/a-chaudhari/EightSleepPod2Server |
| **Home Assistant core `eight_sleep`** | cloud, any | Cloud polling (`iot_class: cloud_polling`). Uses the legacy pyEight. | Apache-2.0 (HA core) **[UNVERIFIED for this folder]** | in HA core | https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/eight_sleep/manifest.json |
| **lukas-clarke/eight_sleep** (+ forked pyEight) | cloud, Pod 4/5 era (new OAuth2 API) | HA custom component with its own bundled pyEight. Climate, sensors, base, audio, alarms. | MIT | 255 stars, pushed 2026-10-08 | https://github.com/lukas-clarke/eight_sleep , https://github.com/lukas-clarke/pyEight |
| **mezz64/pyEight** (original) | cloud (old API) | Python client for `client-api.8slp.net/v1`. Superseded by lukas-clarke's OAuth2 fork. | MIT | 64 stars, pushed 2024-03-20 | https://github.com/mezz64/pyEight |
| **eightctl** (steipete) | cloud | Go CLI: temperature, alarms, base, audio, autopilot, travel, presence | MIT | 98 stars, pushed 2026-10-10 | https://github.com/steipete/eightctl |
| Others (cloud wrappers, MCP servers, CLIs) | cloud | `aerotow/eightsleep-nosub-app` (GPL-3.0, schedules via the cloud API to bypass the subscription), `eight-sleep-mcp` servers, `blacktop/clim8`, `grantnedwards/eight-sleep` | various | | search: https://api.github.com/search/repositories?q=eightsleep+OR+8slp |

### 1.2 What the local projects document (protocols)

**A. DAC / Frank layer** (free-sleep, ninesleep): the stock `frankenfirmware` (C++) is driven over a unix socket.
- Socket path candidates in free-sleep: `$DATA_FOLDER/dac.sock`, `/deviceinfo/dac.sock`, `/persistent/deviceinfo/dac.sock`. It defaults to the Pod 3 path, overridable via `/persistent/free-sleep-data/dac_sock_path.txt`. Source: https://raw.githubusercontent.com/throwaway31265/free-sleep/main/server/dist/config.js
- The server is the listener: free-sleep creates the unix socket server and Frank connects to it. Source: `server/dist/8sleep/unixSocketServer.js` and `frankenServer.js` in the same repo.
- Framing: text, `"<commandNumber>\n<arg>\n\n"` (double-newline separator). Response is `key = value` lines.
- Command numbers (https://raw.githubusercontent.com/throwaway31265/free-sleep/main/server/dist/8sleep/deviceApi.js):

| # | Name | # | Name |
|---|---|---|---|
| 0 | HELLO | 9 / 10 | LEFT/RIGHT_TEMP_DURATION |
| 1 | SET_TEMP | 11 / 12 | TEMP_LEVEL_LEFT/RIGHT |
| 2 | SET_ALARM | 13 | PRIME |
| 5 / 6 | ALARM_LEFT / ALARM_RIGHT | 14 | DEVICE_STATUS |
| 8 | SET_SETTINGS | 16 | ALARM_CLEAR |

  Commands 3, 4, 7, 17, 18 appear commented out in the source: RESET, FORCE_RESET, FORMAT, ALARM_SOLO, STOP_PRIME.
- DEVICE_STATUS fields (zod schema in `server/dist/8sleep/loadDeviceStatus.js`): `tgHeatLevelL/R`, `heatTimeL/R`, `heatLevelL/R`, `sensorLabel`, `waterLevel`, `priming`, `settings`, `doubleTap`/`tripleTap`/`quadTap` (Pod 4+ cover gestures). The term **"capwater" did not appear** in any source I read.
- ninesleep documents its own HTTP layer: `POST /alarm/<side>` with JSON `pl` (vibration %), `du`, `tt` (unix time), `pi` (`double` or `rise`). Also `/temperature/<side>`, `/prime`, `/settings`. Source: https://github.com/bobobo1618/ninesleep
- Cloud endpoints used by the stock firmware (Pod 3 analysis, from opensleep BACKGROUND.md): `device-api.8slp.net:5684` (CoAP, used by DAC), `raw-api-upload.8slp.net:1337` (raw sensor + logs, from Frank), `update-api.8slp.net:443` (SWUpdate). Source: https://raw.githubusercontent.com/LiamSnow/opensleep/main/BACKGROUND.md

**B. Raw sensor streams** (free-sleep biometrics, https://raw.githubusercontent.com/throwaway31265/free-sleep/main/biometrics/BIOMETRICS.md):
- Legacy Pod 3/4: CBOR-encoded `*.RAW` files in `/persistent/`. Records are `capSense` (3 ints per side: out/cen/in + status + seq) and `piezo-dual` (adc, `freq` 500, `gain` 400, arrays `left1/left2/right1/right2` of ~500 int samples per second, seq, ts). The doc says Pod 3 has 2 piezo sensors and Pod 4 has 1.
- Pod 5 firmware writes `capSense2` version 1: 8 floats per side in `values` + status. free-sleep's mapping to out/cen/in is explicitly "empirical, not a documented physical layout".
- Newer firmware (also Pod 3 "no SD", firmware hash `444c5a9e...`) stores sensor data in a **local NATS JetStream server (127.0.0.1:4222)** instead of RAW files, retention <=6 GB / 1 day. free-sleep PR #57/#58 added a reader (`nats-py`). Sources: https://github.com/throwaway31265/free-sleep/pull/57 , https://raw.githubusercontent.com/throwaway31265/free-sleep/main/biometrics/nats_client.py
- The RAW files appear only while the Pod cannot reach the internet. BIOMETRICS.md: "This data is only available if the Pod cannot access the internet."

**C. MCU USART layer** (opensleep, lunaris) - the lowest documented layer:
- Pod 3 (opensleep BACKGROUND.md): i.MX 8M Mini Variscite VAR-SOM-MX8M-MINI running minimal **Yocto**. Two STM32F030CCT6 MCUs: "Frozen" (2 TECs, 2 pumps, solenoid, tank level, reed switch, PID, priming, safety) on `/dev/ttymxc2` @ 38400 baud, and a "Sensor board" on the bed control unit (6 capacitance @ 2 Hz, 8 bed-temp sensors, ambient temp/humidity, ADC for 2 piezos, vibration motors) at 38400 in bootloader, 115200 in firmware mode. Firmware blobs live in `/opt/eight/lib/subsystem_updates/firmware-{frozen,sensor}.bbin`.
- Services on the SOM: Frank (`/opt/eight/bin/frakenfirmware`, C++), DAC/"PizzaRat" (`/home/dac/app`, Node TS, wrapper for Frank), SWUpdate, Capybara (`/opt/eight/bin/Eight.Capybara`, .NET, BLE onboarding, enables the subsystems via PCAL6416 on i2c-1 0x20). Source: BACKGROUND.md above.
- Frame format (lunaris docs, derived from opensleep): `0x7E`, length byte, payload, CRC16-CCITT (poly 0x1021, init 0x1D0F) over the payload only, big-endian. Known Frozen opcodes: Prime `0x52`, SetTargetTemperature `0x40` (side, enable, u16 BE centi-degC), GetTemperatures `0x41`/`0xC1`, text `0x07`, pong `0x81`, JumpToFirmware ack `0x90`. Sensor: Ping `0x01`, SetPiezoFrequency `0x21`, EnablePiezo `0x28`, SetPiezoGain `0x2B`, SetAlarm `0x2C`, EnableVibration `0x2E`; replies `0xAE` (vibration enabled), `0xAC` (alarm set), `0x33` (capacitance, 27-byte, six u16). Sources: https://raw.githubusercontent.com/Schluggi/lunaris/main/docs/usart-frozen.md , https://raw.githubusercontent.com/Schluggi/lunaris/main/docs/usart-sensor.md
- Variant drift already visible: Pod 4 uses `/dev/ttyS1` (Frozen) and `/dev/ttyS2` (Sensor) at 921600 on the sensor link and emits extra unknown packets (opensleep #11). Pod 3 "G0" board (PN 20600, HWREV 0814): firmware at 921600, piezo stream moves `0x32`->`0x34`, capacitance `0x33`->`0x35`, piezo 500 Hz (opensleep #12). Sources: https://github.com/LiamSnow/opensleep/issues/11 , https://github.com/LiamSnow/opensleep/issues/12
- Pod 4 hardware string seen in #11: `PN 20500 SKU 4 HWREV 0609`.
- LED: IS31FL3194 over I2C, documented at https://raw.githubusercontent.com/Schluggi/lunaris/main/docs/led-is31fl3194.md

### 1.3 Root methods documented
- Pod 3 with SD: boot from SD (small button held) with a modified rootfs, see https://blopker.com/writing/04-zerosleep-1/ (linked from INSTALLATION.md; I did not open it).
- Pod 3 no-SD, Pod 4, Pod 5: owner jailbreak via the hub's debug serial port and boot loader, documented step by step in free-sleep's INSTALLATION.md. Not reproduced here; follow the source. Pod 5 must first be set up in the official app. A hardware "firmware reset" reverts it. Source: https://github.com/throwaway31265/free-sleep/blob/main/INSTALLATION.md
- The boot environment uses A/B root slots **[from the same file]**. Nothing found on secure boot / HAB for Pod 4/5.
- Security research on Pod firmware/cloud: Truffle Security's writeup https://trufflesecurity.com/blog/removing-jeff-bezos-from-my-bed (Eight Sleep's response: http://wiki.rossmanngroup.com/Eight_Sleep). Secondary reporting calls the OS "embedded Debian" (https://cybersecuritynews.com/vulnerability-in-internet-connected-smart-beds), which conflicts with opensleep's "Yocto" for Pod 3. **OS family unresolved.** Open Bed Climate is clean-room and does not use vendor firmware images.

## 2. Pod 6 specifically

### 2.1 Existence and launch
- Launched 2026-09-23 (press release dated 2026-09-23, blog dated 2026-09-22/23). Shipping online. Sources: https://secure.businesswire.com/news/home/20260923093537/en/Eight-Sleep-Introduces-Pod-6-The-Smallest-Most-Powerful-Pod-Yet.-Now-Starting-at-%241999 (search-result snippet only, page returned 403 to my fetch), https://www.theverge.com/tech/999018/eight-sleep-pod-6-intelligent-sleep-system-sensors-health-tracking , https://www.cnet.com/health/sleep/eight-sleep-launches-pod-6-with-smaller-hub-and-cheaper-entry-price/
- Pricing: Solo from $1,999, Standard from $2,699 (full) to $2,999 (king/cal king), mandatory Autopilot subscription $199-$399/yr for two sleepers (The Verge link above).

### 2.2 Hardware differences (official sources)

| Item | Pod 5 | Pod 6 | Source |
|---|---|---|---|
| Hub size | 40.6 x 40.6 x 15.2 cm (25,200 cm3) | 42 L x 20 H x 16.5 W cm, 6.9 kg (13,860 cm3), ~8 in tall | https://www.eightsleep.com/ae/pod-cover , https://www.eightsleep.com/blog/shrinking-the-pod-6-hub |
| Water | removable tank | **tank removed**: internal reservoir + direct fill. Priming "up to 940 min earlier gens" -> <5 min (spec table: 20 -> 5 min) | shrinking-the-pod-6-hub |
| Thermal | 2 TEC per side, 400 W | **3 TEC per side**, 550 W PSU (12 V DC out, 120/240 V AC in), redesigned heat sink with fans between halves, fan speed by PSU/Hub sensors | shrinking-the-pod-6-hub, ae/pod-cover |
| Cover sensors | 1 biometric sensor per side | **9 per side** ("18 total" in some press, e.g. Independent) | https://www.eightsleep.com/blog/discover-everything-new-with-pod-6 , https://www.independent.co.uk/extras/indybest/house-garden/bedroom/eight-sleep-pod-6-review-b3054823.html |
| Cabling | water cord + USB cable | **water cord and USB combined into a single connector** for Pod, Base, Blanket, Pillow Cover | discover-everything-new-with-pod-6 |
| Sizes | standard only | adds Solo (Twin/Twin XL, half of Q/K/CK). Solo not compatible with Base or Blanket. | ae/pod-cover |
| Add-ons | Base, Blanket, Pillow Cover | same set; Base has an integrated speaker | ae/pod-cover |
| Radio | Wi-Fi + BLE | FCC class "Smart Pod with integrated WiFi/Bluetooth"; **two Wi-Fi antennas (Wifi0, Wifi1, 2.4/5 GHz FPC) + one BT antenna** | https://fccid.io/2AYXT61100005 (antenna exhibit titles) |

Not stated anywhere I found: Hub SoC, OS, whether the Cover MCU/USB protocol is unchanged, and whether Pod 5 covers work with the Pod 6 Hub (or the reverse). The 9-sensor count rules out the Pod 3/4/5 capSense/piezo layouts by default **[INFERRED]**.

### 2.3 Jailbreak support
- None. free-sleep README lists Pod 3/4/5 only: https://github.com/throwaway31265/free-sleep . opensleep/lunaris: Pod 3-5 only. Issue #56 asks about Pod 6 ("As they downsized the pod i wonder if the hw is still somewhat similar"), no answers yet.

### 2.4 Firmware / OS / SoC
- Pod 6: **[UNVERIFIED]**. Pod 3: i.MX 8M Mini (Variscite SOM), Yocto (opensleep). Pod 4/5 root procedure is identical in free-sleep (same boot-loader method), so likely the same SOM family **[INFERRED]**, not confirmed.

## 3. FCC filings

Grantee code **2AYXT**, Eight Sleep Inc, 915 Broadway STE 1301, New York, FRN 0030587562, contact Alex Lednev (Staff Electrical Engineer). Source: https://fccid.io/2AYXT , https://fcc.report/company/eight-sleep-inc

| FCC ID | Filed | Equipment / radios | Test lab | Likely product | Public exhibits |
|---|---|---|---|---|---|
| 2AYXT61100001 | 2023-03-02 | "10503" = Pod 3 hub model. 2.4 GHz + 5180-5240 MHz, Wi-Fi 2x2 MIMO | NTS Labs | Pod 3 (free-sleep README names this FCC ID for Pod 3 no-SD; eBay lists model 10503 as Pod 3) | internal + external photos, antenna info, test reports. https://fccid.io/2AYXT61100001 |
| 2AYXT61100002 | 2024-03-12 | DTS 2402-2480 + 5745-5825 | CVC Testing | **[UNVERIFIED]** probably Pod 4 (model 10504 per eBay). No exhibit says so. | external photos, user manual, antenna specs, test reports. Internal photos, schematics, block diagram, op. description are "metadata only" (confidential). https://fccid.io/2AYXT61100002 |
| 2AYXT61100003 | 2025-06-20 | NII 5180-5240 / 5745-5825, 2402-2480 (BLE), 2412-2462 | CVC | **[UNVERIFIED]** probably Pod 5 (2025) | internal/external photos, manual, antenna specs (BLE, WIFI 1, WIFI 2), BLE test data. https://fccid.io/2AYXT61100003 |
| 2AYXT61100004 | 2025-06-26 | NII + BT/BLE/Wi-Fi | CVC | **[UNVERIFIED]** Pod 5 variant? | internal photos (11 pp), manual, RF exposure, BT/BLE/WIFI test data. Schematics, parts list, op. description confidential. https://fccid.io/2AYXT61100004 |
| **2AYXT61100005** | **2026-08-21** | "Smart Pod with integrated WiFi/Bluetooth for thermal regulation control", 2402-2480 / 2422-2462 / 5745-5825 MHz, DSS + composite. Exhibits named "Pod 6 label location", "Pod 6 nameplate", "Pod6 Block Diagram", "Pod 6 UNII Software Security". | HCT America | **Pod 6** (exhibit names) | Public now: label location, nameplate, antenna exhibits (Wifi0/Wifi1/BT FPC antennas), BT/BLE/WLAN 2.4/WLAN 5 GHz test reports (HCT report series HA260519-GGC-002), RF exposure, attestations. **Confidential until 2027-02-17**: internal photos (APPENDIX B.2), external photos, safety manual, test-setup photos. **No date**: schematics, block diagrams, operational description, UNII software security. https://fccid.io/2AYXT61100005 |

What the FCC data actually reveals:
- Wi-Fi 2.4 + 5 GHz with two antennas (2x2) and a separate BT/BLE antenna. Pod 3's grant note says "2x2 MIMO, 20/40/80 MHz" (https://fccid.io/2AYXT61100001).
- Pod 6 reports are PDFs I could not read. fccid.io and fcc.report block scripted PDF download (403, Cloudflare). **Chipset, SoC, module and MCU names are not in anything I could read.** Pod 3/4/5 internal-photo PDFs are image-only PDFs I did not inspect visually. **Open item: download them manually and read the chip markings.**
- Pod 6 test-report document IDs for manual download: 9579417 (BLE, 48 pp), 9579418 (WLAN 2.4), 9579457 (WLAN 5 GHz, 56 pp), 9579478 (BT), 9579479 (RF exposure); antenna reports 9579447/9579448/9579473/9593915/9593916. Fetch via `https://fccid.io/ViewExhibitReport.cfm?id=<id>` in a browser (blocked for curl).
- Reports usually contain EUT description, module/antenna gain and tested firmware/hardware version. Worth reading first.
- Re-check on or after 2027-02-17 for the internal photos. Short-term confidentiality dates shown on the exhibit list: 2025-12-17 for 61100003, 2025-12-22 for 61100004, 2024-09-08 for 61100002, 2023-08-29 for 61100001.
- Another device.report entry mentions "Pod Hub, 11504, IMDA" (Singapore): https://device.report/eight-sleep . Model 11504 is probably Pod 5 **[UNVERIFIED]**.

## 4. Eight Sleep cloud API (from pyEight / HA / eightctl)

All unofficial and reverse-engineered. Eight Sleep publishes no public API (https://github.com/api-evangelist/eight-sleep/blob/main/README.md).

| Host | Base URL | Used for | Source |
|---|---|---|---|
| auth-api | `https://auth-api.8slp.net/v1/tokens` | OAuth2 token | https://raw.githubusercontent.com/lukas-clarke/pyEight/main/pyeight/constants.py |
| client-api | `https://client-api.8slp.net/v1` | `users/me`, `users/{id}`, `users/{id}/trends`, `users/{id}/current-device`, `devices/{id}?filter=leftUserId,rightUserId,awaySides` | pyEight `user.py`/`eight.py` in lukas-clarke/eight_sleep |
| app-api | `https://app-api.8slp.net/` | `v1/users/{id}/temperature`, `/temperature/all`, `/temperature/pillow`, `/away-mode`, `/alarms` (+ `v2`, `/snooze`, `/dismiss`), `/base`, `/base/angle`, `/audio/player...`, `/audio/tracks`, `v1/household/users/{id}/summary`, `v1/devices/{id}/priming/tasks` | same |
| other | (eightctl) `/autopilotDetails`, `/autopilot-history`, `/temp-events`, `/travel/...`, `/temperature/nap-mode/...`, `/temperature/hot-flash-mode/...`, `/devices/{id}/peripherals`, `/vibration-test`, `/audio/player/pair` | https://github.com/steipete/eightctl/tree/main/internal/client |

Auth flow (https://raw.githubusercontent.com/steipete/eightctl/main/internal/client/auth.go): `POST https://auth-api.8slp.net/v1/tokens`, form body `grant_type=password`, `username`, `password`, `client_id`, `client_secret`. Response: `access_token`, `expires_in`, `userId`. Then `Authorization: Bearer <token>`. Tokens are refreshed with a 120 s buffer in pyEight (`TOKEN_TIME_BUFFER_SECONDS`).
- The app-embedded client credentials are not reproduced here. Open Bed Climate does not use the vendor cloud.
- Headers used by the clients: `user-agent: okhttp/4.9.3` (impersonates the Android app).
- The old `mezz64/pyEight` used `client-api` with email/password session login. The newer OAuth2 flow came with the 2024 API change; HA core still depends on the older library.
- Cloud-only: the cloud API controls a Pod via the vendor cloud, so it needs the stock firmware and the subscription state. free-sleep/opensleep bypass this by replacing the on-device software.

## 5. Android app

- Package: **`com.eightsleep.eight`**, "Eight Sleep" by Eight Sleep Inc., 50K+ installs. https://play.google.com/store/apps/details?id=com.eightsleep.eight
- Framework: Eight Sleep's current job posts ask for native Android: "Kotlin/Jetpack Compose/Coroutines/Flow/MVVM/MVI" (https://jobs.ashbyhq.com/eightsleep/2fef2cd1-f874-4254-8e7b-1865799a0edd) and native iOS "Swift, SwiftUI, Combine" (https://startup.jobs/senior-software-engineer-mobile-ios-milan-eight-sleep-2-8812442). Conclusion: **native Kotlin/Compose (probably), not Flutter**. A Himalayas aggregator page lists "React Native" among their tech (http://himalayas.app/companies/eight-sleep/tech-stack), a stale or loose signal. **I did not inspect the APK, so Flutter/RN is not excluded. Check for `libflutter.so` / `libreactnativejni.so` in the APK to settle it.**
- Version cue: eightctl notes secrets were extracted from app v7.39.17 (okhttp client).

## 6. Already solved vs open for Pod 6

| Area | Status | Notes |
|---|---|---|
| Cloud API control (temperature, alarms, base, audio) | **Solved for Pod 4/5-era**; Pod 6 **[UNVERIFIED]** | Same cloud and app expected. Test lukas-clarke/eight_sleep or eightctl against a Pod 6 account. Watch for new device/peripheral types and new sensor fields. |
| Root access method on Pod 3/4/5 | Solved by the community (free-sleep docs) | Pod 6 board, debug port and boot flow unknown. FCC internal photos not public until ~2027-02-17. |
| Firmware images | Out of scope for Open Bed Climate (clean-room) | Analysing vendor firmware would only be relevant for a separate compatibility track on an owned device. |
| Frank/DAC socket protocol (`dac.sock`, commands 0-16) | Solved for Pod 3-5 | Depends on stock Frank on the Hub. Needs a Pod 6 Frank image to confirm the same commands. |
| MCU USART protocol (Frozen/Sensor) | Documented for Pod 3, partly for Pod 4 | Pod 4 and G0 boards already diverge. Pod 6 adds a third TEC per side and a new Cover (9 sensors/side, merged connector), so expect new opcodes and likely a new sensor protocol **[INFERRED]**. |
| Piezo / capacitance formats | Solved for Pod 3 (`capSense`, `piezo-dual`) and empirically Pod 5 (`capSense2` x8) | 9 sensors/side: layout unknown. NATS JetStream replaces RAW files on newer firmware. |
| Heart rate / HRV / breath processing | Solved at hobby grade (free-sleep, HeartPy-based); lunaris has none | Need re-tuning for the multi-sensor Pod 6 cover. |
| SoC / OS / secure boot of Pod 6 hub | **Open** | No public data. |
| Wi-Fi/BLE module and MCUs of Pod 6 | **Open** | FCC reports are public but not readable here; internal photos confidential. |
| BLE onboarding protocol (Capybara) | **Open** | Capybara is .NET, handles BLE setup on Pod 3. No protocol document found. |
| Pod 6 water system (internal reservoir + fill) | **Open** | New. Priming command semantics may change. |
| Android app internals | Partly | Package known; framework and API changes for Pod 6 not examined. |

### Suggested next steps (not done here)
1. Read the Pod 6 FCC test reports by hand (IDs above) for module and chipset names.
2. (dropped: Open Bed Climate is clean-room and does not obtain or analyse vendor firmware)
3. Pull the latest APK of `com.eightsleep.eight`: check native vs RN/Flutter, grep for "Pod6"/new peripheral types and the endpoint list.
4. Run lukas-clarke/eight_sleep against a Pod 6 account and diff `/devices/{id}` and `/users/{id}/trends` JSON.
5. Watch free-sleep issue #56 and opensleep #12.
