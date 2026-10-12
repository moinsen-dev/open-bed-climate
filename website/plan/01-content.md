# 01 — Content plan: positioning, audiences, IA, copy

Scope: public website for **Open Pod**, built with Astro and written in English only. It has three goals:
promote the idea, recruit contributors and attract sponsors.
Sources read: README.md, docs/FEATURES.md, SAFETY.md, CONTRIBUTING.md, hardware/README.md, hardware/kits/*.toml,
hardware/parts.toml, docs/design/BOM.md, docs/design/OPEN-DECISIONS.md, STATE.md, .github/ISSUE_TEMPLATE/*.

---

## 0. Repo inconsistencies the site must not copy (fix at source or render around)

| # | Conflict | Rule for the site |
|---|---|---|
| C1 | Coldest-water numbers: README and hardware/README say ~21.5 / ~18.6 / ~18.3 °C. Kit TOML `[claims].min_water_c` says 21.7 / 18.8 / 18.5. | Render **only** from `[claims].min_water_c`. It is the bound that CI checks. Label it "model estimate · sleeper in bed · 25 °C room". Never hand-type these numbers. Ask the lead to align the README. |
| C2 | TEC supply voltage: BOM.md v0.1 says "12 V ≥ 750 W". The kit TOML, parts.toml and STATE say 24 V. The README ASCII diagram says "certified 12 V power supply". | Don't reuse the README diagram or the BOM wording. Site copy says "certified plug-in supplies (24 V for the Peltiers, 12 V for pumps and electronics)". |
| C3 | The BOM total "~990–1,040 EUR" comes from the stale v0.1 file (Duo Reference only). | You may use it only as "rough order of magnitude, Duo Reference, BOM v0.1". It is not a price and must not appear on the home page. |
| C4 | Status: README marks hub schedules as done (and `hub/esphome/components/obc/schedule.h` has tests). STATE still lists them under "next". | README + code decide "done". STATE decides only "next" and "open friction". |
| C5 | "Pod-class cooling" appears in duo-standard.toml and hardware/README.md. | **Banned on the site.** It is a parity claim we can't back. Use "two zones, four Peltiers per side, our strongest Tier 0 cooling" instead. |
| C6 | FEATURES.md uses "Pod 6" as its left column (~20 mentions). | Don't render it raw. Transform it to generic capability names (see §4, /features). |
| C7 | README says it "tracks presence, heart rate and breathing" in the present tense. | All biometrics are planned (status 🔜). Site wording: "planned: presence, heart rate and breathing from in-bed sensors (not a medical device)". |
| C8 | OPEN-DECISIONS has a section on deferred teardown and FCC photos for a commercial unit. | Keep it off the site entirely. |
| C9 | FEATURES.md says "13–43 °C setpoint range". The kits only *reach* their `[claims].min_water_c` (21.7 / 18.8 / 18.5 °C, sleeper in bed, 25 °C room) up to 43 °C. | Headline the per-kit reachable range ("{min_water_c}–43 °C, model estimate"). Never headline 13 °C. On /features, rewrite that cell to "setpoint 13–43 °C; reachable range depends on the kit". |

---

## 1. Audiences

Ordered by priority right now: the project's bottleneck is a **first physical build with measurements**.

| # | Audience | What they need to see | Primary CTA | Secondary CTA |
|---|---|---|---|---|
| A1 | **DIY builders** (makers, PC-watercooling people) | The kits table, how hard each tier is, the safety page, the commissioning checklist, a parts list by role, and "nobody has built one yet, so you'd be first" | "Pick a kit" → /kits | "Post a build report" (issue template `build-report.yml`) |
| A2 | **Embedded / firmware devs** (Rust, embassy, RP2350) | The two-MCU architecture (the safety MCU is separate from the networked hub), `firmware/` state (compiles, ~50 KB, golden vectors, not on hardware yet), concrete open tasks | "Bring up the firmware" → /contribute#firmware | Repo link to `firmware/` |
| A3 | **Home Assistant / ESPHome users** | Local-only, no account, native HA entities (climate per zone, sensors, prime/clear-faults), schedules on the hub, Bluetooth proxy for adjustable bases | "See the HA integration" → /software#home-assistant | Star/watch the repo |
| A4 | **Hardware / electrical engineers, safety reviewers** | The SAFETY limits table (verbatim), the independent hardware backstops, the "no mains wiring by builders" rule, the Tier 1 power board need | "Review the safety concept" → /safety | "Report a safety concern" (`safety-concern.yml`) |
| A5 | **Mechanical / textile people** | The water mat is the hardest open part: couplings, enclosure, a single combined connector | "Prototype the mat" → /contribute#mechanical | — |
| A6 | **Parts hunters** | Roles-not-brands catalog; live count of unverified / listing-only examples | "Verify a part" → /parts/ | `part-substitution.yml` |
| A7 | **Sleep / thermal researchers, students** | The five measurements needed from prototype 0, the open thermal model, open biometrics (BCG) algorithms, the clean data ownership | "Help measure" → /contribute#research | Python model link (`software/obc`) |
| A8 | **Sponsors** (component vendors, PCB fabs, maker spaces, foundations, individuals) | What money or parts unlock right now (a concrete list, not tiers), license guarantee (stays open), how they are credited | "Sponsor prototype 0" → /sponsor | Contact (placeholder) |
| A9 | **Press / bloggers** | One-paragraph pitch, honest status, the right-to-repair and local-first angle, assets they may use | /press (one section on /about for v1) | Contact |
| A10 | **Writers / translators** | Docs are English; translations go under `docs/i18n/<lang>/` | /contribute#docs | — |

---

## 2. Positioning

**Core message (one sentence):**
Open Pod is an open-source, local-first bed climate system that cools and warms each side of the bed with
water, built from standard parts you can buy, repair and change. It is in the design phase, and we're looking
for the people who will build the first one.

**Category we claim:** "open bed climate system" / "DIY water-cooled mattress topper". We don't claim to be a
"replacement for" or "alternative to" any named product.

**Value pillars (4):**
1. **Yours, locally.** No cloud, no account, no subscription. Schedules run on the hub in your home, and
   Home Assistant is native. Biometric data never leaves the house unless you export it.
2. **Safety by architecture.** The networked hub can only *request* temperatures. A separate control MCU
   enforces fixed limits, and independent hardware cutoffs work even if all software fails. Builders never
   wire mains.
3. **Standard parts, adaptable kits.** PC-watercooling parts, Peltier modules, a Raspberry Pi Pico 2, an ESP32
   and certified plug-in supplies. Parts are listed by role, so you can substitute. Use one zone or two, Tier 0
   modules or Tier 1 PCBs.
4. **Claims you can check.** Every kit is a TOML file, and CI checks its performance claims against an open
   thermal model. Write your own kit and get the same check. Real measurements beat the model, and we want
   them.

**Tagline options:**
1. **"Sleep at your temperature. On your hardware."** (recommended: says both the benefit and the stance)
2. "The open bed climate system. Build it, fix it, own it."
3. "Cool nights, open hardware, no cloud."

**Honesty rules (binding for all copy):**
- H1 **Phase banner on every page:** "Design phase: no unit has been built or measured yet."
- H2 **Tense:** present tense only for things that exist and are tested in software or simulation (thermal
  model, control and safety logic, protocol, firmware core vs. golden vectors, hub component compiles,
  schedules). Hardware is always "designed, not yet built". Firmware and hub are "compiles, not yet run on
  hardware".
- H3 **"Not certified. Not a medical device."** Every page about sensing or biometrics says so. Biometrics are
  "planned" and estimates. Never "monitors your health".
- H4 **Numbers:** every temperature carries "model estimate" and its conditions. Render it from TOML, never
  rounded into a nicer number.
- H5 **No parity claims.** No "Pod-class", "same as", "matches" or "replaces". The commercial product is named
  at most once per page, nominatively, and only where necessary (features background, about). Default
  wording: "inspired by commercial bed-cooling systems". Disclaimer in the footer: "Not affiliated with or
  endorsed by any bed-cooling manufacturer."
- H6 **Clean-room:** public information only. No vendor logos, product photos, UI screenshots, trade dress or
  colour schemes. Imagery is our own diagrams and renders.
- H7 **No test counts or star counts in copy.** They drift. Link to a CI badge instead.
- H8 **No prices on the home page.** On /hardware and /sponsor, BOM figures are "rough order of magnitude,
  not quotes".

---

## 3. Sitemap + data sources

Principle: **the repo is the CMS.** Pages that show data read it at build time through Astro content
collections or loaders. Hand-written copy lives in `website/src/content/` and links to repo files by path.
Shared `<Status>`, `<ModelEstimate>` and `<SafetyNote>` components enforce H1–H4.

| Route | Sections (in order) | Fed by (build-time) |
|---|---|---|
| `/` Home | Phase banner · Hero · Pillars (4) · How it works (diagram + 4 steps) · Kits teaser (3 cards) · Safety strip · Status & roadmap · Get involved (role tiles) · Sponsor teaser · Footer | kits/*.toml (`[kit]`, `[thermal]`, `[sensing]`, `[claims]`) · README status table (hand-synced, see §6) · `website/src/data/roadmap.yaml` |
| `/how-it-works` | Overview diagram · Water loop · Thermal module (Peltier, heat/cool) · Control vs. hub split · Protocol (OPL) in one paragraph · Sensing options · Further reading (design docs) | docs/design/00–05 (links + short summaries) · hardware/README.md module map (mermaid → static SVG) |
| `/kits` | Kit comparison table · Tier 0 vs. Tier 1 explainer · "Make your own kit" (copy TOML, run tests) · Model-estimate footnote | kits/*.toml (all fields) · hardware/README.md tier text |
| `/kits/[id]/` | Summary · Specs from TOML · Sensing option · Power chain · Claims + check status · Role list → parts · "Build this kit" CTA | the one kit TOML · parts.toml roles · CI result for `test_kits.py` (optional, via badge) |
| `/parts/` | Roles-not-brands explainer · Status legend · Roles grouped by module (requirement first, examples with status, source, `verified_on`) · "Verify a part" CTA with live counts | parts.toml (generate the same way as PARTS.md; counts computed) |
| `/safety` | Why it matters · What you can customise · **What you must not change (table, verbatim)** · Architecture rule · Mains tiers · Commissioning checklist (verbatim) · Report a safety issue | SAFETY.md (rendered as MD; tables are never retyped) |
| `/how-it-works/#software` | Local-first statement · Home Assistant entities · Schedules on the hub · Reference model (Python) · Firmware (Rust/embassy) · Dev quickstart (test commands) | hub/esphome/README.md · CONTRIBUTING.md "Development" · README "Get involved" commands |
| `/features` | "What a bed climate system does" capability table (generic names, Open Pod approach, status) · Where Open Pod goes further · One nominative inspiration line | docs/FEATURES.md, **transformed**: drop column 1, map rows to generic names in `website/src/data/feature-names.yaml` (keyed by row order, CI check that row counts match) |
| `/status` (roadmap) | Phase banner · Done (tested in software) · Next · Measurements needed from prototype 0 · Open decisions (decided ones only) | README status table · STATE.md "Next intended step" + "Open friction" · OPEN-DECISIONS.md D1–D6 + measurements 1–5 (drop the deferred-RE section) |
| `/contribute` | Intro ("you don't need to be an engineer") · Role tiles with concrete tasks (§5) · Ground rules (4) · First steps (clone, run tests) · Issue templates | CONTRIBUTING.md · §5 mapping (`website/src/data/help-wanted.yaml`) · .github/ISSUE_TEMPLATE/*.yml (names + links) |
| `/sponsor` | Why sponsor now · What your support unlocks (concrete list) · In-kind help wanted · How we credit sponsors · Openness guarantee (licenses) · Contact | `website/src/data/sponsor-asks.yaml` · OPEN-DECISIONS measurements · BOM.md (order of magnitude, labelled) · LICENSE files |
| `/about` | Why Open Pod exists · Clean-room policy · Prior art (community local-control projects, linked) · Licenses · Not-affiliated disclaimer · Press kit (v1: pitch + logo + diagram) | README "Background" · docs/research/prior-art.md (links only) · CONTRIBUTING ground rule 1 |
| `/schedule/` | Curve visualizer (owned by 03-tech) · intro copy: "Your night, as a curve. Schedules run on the hub, no subscription." · wake-ramp explainer | software/obc schedule + hub schedule.h (see 03-tech) |
| `/docs/[...slug]/` | SAFETY, CONTRIBUTING, docs/design/*.md rendered in place; everything else links to the repo | repo Markdown (see 03-tech) |
| `404` | Short, links to /kits and /contribute | — |

Route names follow 03-tech (`/kits/`, `/kits/[id]/`, `/parts/`, `/features/`, `/schedule/`, `/docs/[...slug]/`, `/safety/` = alias of the SAFETY doc, `/contribute/`). This plan adds `/how-it-works/`, `/status/`, `/sponsor/` and `/about/`. `/software/` is folded into `/how-it-works/#software` (agreed with 03-tech); see the `/how-it-works/#software` row above.

Header nav: How it works · Kits · Safety · Status · Contribute · **Sponsor** (button).
Footer nav: Features · Parts · Schedule · Docs · About · Repo · Code of Conduct · Licenses.

---

## 4. Draft copy

### 4.1 Home

**Phase banner (sitewide, dismissible per session):**
> Design phase: no Open Pod has been built or measured yet. [Help build the first one →](/contribute)

**Hero**
- H1: **Sleep at your temperature. On your hardware.**
- Sub: Open Pod is an open-source bed climate system. Water runs through a thin mat on your mattress, and
  Peltier modules cool or warm it, separately for each side of the bed. It runs locally with Home Assistant,
  is built from standard parts, and has no cloud and no subscription.
- Buttons: **[Help build prototype 0]** (→ /contribute) · [Pick a kit] (→ /kits) · tertiary text link: Sponsor →
- Microline: Open hardware (CERN-OHL-S-2.0) · Open software (Apache-2.0) · Not certified, not a medical device.

**Pillars**
1. **Yours, locally.** No cloud, no account, no subscription. Your temperature schedule runs on the hub next
   to your bed, and Home Assistant sees every zone natively.
2. **Safety by architecture.** The networked hub can only ask for a temperature. A separate control chip
   enforces fixed limits, and hardware cutoffs act even if every line of software fails. You never touch
   mains wiring.
3. **Standard parts, your kit.** PC-watercooling parts, Peltier modules, a Raspberry Pi Pico 2, an ESP32 and
   certified plug-in power supplies. Every part is listed by the job it does, so you can swap it.
4. **Claims you can check.** Each kit is a small text file. Our test suite checks its temperature claims
   against an open thermal model. Write your own kit and get the same check.

**How it works** (4 steps next to the diagram; diagram redrawn without the "12 V" label, see C2)
1. **Mat.** A thin water mat lies on your mattress, one zone per side.
2. **Thermal module.** Peltier modules move heat into or out of the water. A pump circulates it.
3. **Control board.** A Raspberry Pi Pico 2 runs the temperature loop and the safety limits, with a 43 °C
   ceiling, flow and leak interlocks, and a watchdog.
4. **Hub.** An ESP32 running ESPHome runs your night schedule and connects to Home Assistant. It can only
   request temperatures.
Link: How it works in detail →

**Kits teaser** (3 cards, data from TOML)
- **Solo Starter.** One zone, three Peltiers, load-cell sensing, Tier 0 (no custom PCB). Coldest water about
  {claims.min_water_c} °C*. *For a first build and a single sleeper.*
- **Duo Standard.** Two zones, four Peltiers per side, pneumatic sensing, Tier 0. Coldest water about
  {claims.min_water_c} °C*. *For couples, with our strongest Tier 0 cooling.*
- **Duo Reference.** Two zones, Tier 1 reference PCBs, piezo-grid sensing. Coldest water about
  {claims.min_water_c} °C*. *For experienced builders.*
- All kits warm to 43 °C, the safety cap.
- Footnote: \*Model estimate for a sleeper in bed in a 25 °C room. Checked in CI against the thermal model,
  not yet measured.
- Link: Compare kits / make your own →

**Safety strip**
> Water, several hundred watts and a sleeping person. We take that seriously: fixed limits in firmware,
> independent hardware cutoffs, certified plug-in supplies only, and a commissioning checklist before the
> first night. Nothing here is certified, so you build at your own risk. [Read the safety concept →](/safety)

**Status & roadmap** (three columns)
- **Works in software (tested):**
  - Thermal model and kit checks
  - Control and safety logic
  - OPL protocol
  - Pico 2 firmware core, which matches the reference
  - ESPHome hub component with night schedules (compiles for ESP32-S3)
- **Next:**
  - Verify the remaining parts against datasheets
  - Fan and pump PWM
  - Firmware update path over OPL
  - First hardware bring-up
- **Needs you:**
  - The first physical build
  - Five measurements only a prototype can give us

Link: Full status →

**Get involved** (role tiles, each → /contribute#anchor)
- Heading: **The most valuable contribution right now: build one and measure it.**
- Builders · Parts hunters · Electronics & safety · Mechanical & textile · Firmware · Home Assistant &
  software · Researchers · Writers. Each tile shows one concrete task from §5.

**Sponsor teaser**
> **Fund the first real measurements.** Parts for prototype 0, a test cooling pad, measuring instruments and
> a first run of reference PCBs. Small and concrete, and everything it produces stays open.
> [Sponsor Open Pod →](/sponsor)

**Footer**
- Open Pod. Open hardware (CERN-OHL-S-2.0), open software and docs (Apache-2.0).
- Experimental hardware: not certified, not a medical device. Build and use at your own risk.
- Not affiliated with or endorsed by any bed-cooling manufacturer. All product names belong to their owners.
- Links: Repo · Code of Conduct · Safety · Contact {PLACEHOLDER}

### 4.2 /kits (intro)
> Pick a kit, then make it yours. A kit is a short TOML file that sets zones, Peltiers per zone, heatsink,
> current limit, sensing option and power supplies. It also states what the kit claims to deliver. Our test
> suite checks those claims against the thermal model and also checks power-supply load in a warm room and
> heating without tripping the cutoffs. Copy `solo-starter.toml`, change it, and run the tests.
>
> **Tier 0 (modules only):** off-the-shelf boards and PC-watercooling parts on a DIN rail or carrier plate.
> No custom PCB, and soldering is optional.
> **Tier 1 (reference PCBs):** a power board and a cover sensor board. Smaller, quieter and cleaner, but it
> needs PCB assembly, and its mains module must be assembled by a qualified person.

### 4.3 /safety (intro, above the verbatim SAFETY.md body)
> Open Pod is meant to be built and changed by its users. That's why this page draws a hard line between what
> you can customise and what you can't. The limits below aren't in any config file. They are compiled into
> the control firmware and backed by hardware that works when software doesn't. Have the electrical part
> reviewed by a qualified person before you sleep on a build.

### 4.4 /contribute (intro)
> You don't need to be an engineer. Right now, one honest build report with photos and measurements is worth
> more than any line of code, because every number on this site is still a model estimate. Pick a role below.
> Each one lists tasks that are open today.

### 4.5 /sponsor
- **Heading:** Help us turn a tested design into a measured one.
- **Body:**
  > The design, the control software and the firmware exist and are tested in simulation. What's missing is
  > hardware on a real bed. Your support goes into concrete things, and all results are published under open
  > licenses.
- **What support unlocks** (from `sponsor-asks.yaml`; no money tiers until the owner decides):
  1. Parts for prototype 0 (Solo Starter first, then Duo Standard).
  2. A medical cooling pad for the v0 mat, to measure body-to-water heat transfer early (decision D4).
  3. Instruments for the five prototype-0 measurements: heat transfer through a topper, cold-plate
     resistance, heatsink resistance vs. fan noise (target ≤ 30 dB(A)), piezo signal quality, and
     condensation at 15 °C water and 60 % RH.
  4. A first run of the Tier 1 power board and cover sensor board.
  5. A qualified electrical review of the safety concept.
- **In-kind help:** Peltier modules, cold plates, pumps, dry-break couplings, TPU mat fabrication, PCB
  fabrication and assembly, lab time, or space at a maker space.
- **Credit:** sponsors are listed on this page and in the repo. Sponsors get no influence over safety limits
  or licenses.
- **Order of magnitude:** a full Duo Reference build is roughly €1,000 in parts (BOM v0.1, rough, not a
  quote).
- **CTA:** {SPONSOR_URL / CONTACT — owner decision}

### 4.6 /features (intro + rule)
> Commercial bed-cooling systems showed what a smart mattress cover can do. Open Pod covers the same kinds of
> capabilities with open hardware and local software, and says plainly which ones are designed, which are
> planned and which we leave to other products.

- Render the table with generic capability names, for example: "Per-side heating and cooling", "Two
  independent zones", "Night temperature schedule", "Thermal wake-up", "Vibration alarm", "In-bed sensing",
  "Heart rate, HRV, breathing (planned, not medical)", "Sleep stages", "Tap gestures", "Away, nap and hot-flash
  presets", "App and Home Assistant control", "Cloud account" (not needed, by design), "Adjustable base"
  (via existing HA integrations), "Speaker", "Blanket", "Pillow cover", "Updates".
- Status labels as text badges: **Designed** · **Planned** · **Via other products** · **Out of scope (by
  design)**. No emoji.

### 4.7 /about (key paragraph)
> Bed-cooling systems work well, but the ones on the market depend on the vendor's cloud and a subscription.
> A community has already built local control for some older commercial hardware. Open Pod takes a different
> route: our own open hardware, designed clean-room from public information, so nobody depends on a vendor's
> servers to sleep well. We don't use vendor firmware, decompiled code, leaked documents or rooting
> instructions, and we don't accept them as contributions.

---

## 5. Help wanted: concrete tasks per role

Store as `website/src/data/help-wanted.yaml` (`role`, `task`, `source`, `link`, `difficulty`). Re-check it
against STATE.md whenever STATE is refrozen.

| Role | Task | Source |
|---|---|---|
| **Builder** | Build the Solo Starter and post a build report (template `build-report.yml`) | README, hardware/README |
| Builder | Run the 5-step commissioning checklist and report the results | SAFETY.md |
| Builder / researcher | Measure body-to-water heat transfer through a typical topper (heated dummy pad at 34 °C) | OPEN-DECISIONS measurement 1 |
| Builder | Measure cold-plate thermal resistance per Peltier with real clamping | measurement 2 |
| Builder | Measure heatsink resistance vs. fan noise (target ≤ 30 dB(A)); this replaces the kit `heatsink_k_per_w` ESTIMATE values | measurement 3 · kit TOML comments |
| Builder | Test condensation at 15 °C water and 60 % RH | measurement 5 |
| **Parts hunter** | Verify the {N_unverified} unverified and {N_listing} listing-only part examples against datasheets (today: 11 and 17 across 20 roles; compute at build time) | parts.toml |
| Parts hunter | Confirm the GST280A24 / GST90A12 supply datasheets (variant, current, IEC inlet, connector) | STATE next step 1 |
| Parts hunter | Find a certified 50 °C normally-closed thermal cutoff, a DPDT polarity relay rated for DC and a leak sensor | STATE next step 1 |
| **Electronics / safety** | Review the safety concept and the "must not change" limits | SAFETY.md · docs/design/02-electrical-safety.md |
| Electronics | Verify the DPS5020 register map, output ripple and EEPROM write behaviour | STATE open friction |
| Electronics | Design the Tier 1 power board (6 Peltier channels, protection, relays) and the cover sensor board | CONTRIBUTING · BOM.md items 10, 15 |
| **Mechanical / textile** | Prototype the water mat (welded TPU channels), dry-break couplings and an enclosure with drip tray | CONTRIBUTING · BOM.md |
| Mechanical | Design a combined water + data connector (nice to have) | FEATURES (status 🔜) |
| **Firmware** | First bring-up of `firmware/obc-pico2` on a real Pico 2 (wiring in hardware/WIRING.md) | README · STATE |
| Firmware | Fan and pump PWM control | STATE next step 3 |
| Firmware | Firmware-update path over OPL | STATE next step 3 |
| **Home Assistant / software** | Run the ESPHome hub component on real hardware | README |
| HA / software | Make the dew-point guard easier to set up (room sensors are commented out in the example) | STATE open friction |
| HA / software | Adaptive schedules, presets (away, nap, hot flash), local web UI | FEATURES |
| **Researcher (sleep / signal)** | Piezo signal quality per grid position (heart-rate detectability across sleeping positions) | measurement 4 |
| Researcher | Open BCG algorithms for heart rate, HRV and breathing on the hub; sleep stages with open algorithms only | FEATURES · CONTRIBUTING |
| **Writer / translator** | Clarify the docs; translations under `docs/i18n/<lang>/` | CONTRIBUTING |

Ground rules shown on /contribute, condensed from CONTRIBUTING:
1. Clean-room.
2. Safety limits need a separate issue and review by two maintainers.
3. Claims need evidence.
4. List parts by role, not by brand.

---

## 6. Keeping content in sync

- **Generated at build time (never edit on the site):**
  - kit specs and claims (kits/*.toml)
  - the parts catalog and its counts (parts.toml)
  - the SAFETY tables and checklist (SAFETY.md rendered)
  - issue-template names (.github/ISSUE_TEMPLATE)
- **Hand-maintained data files in `website/src/data/` with a source pointer per entry:**
  - roadmap.yaml (from README status + STATE)
  - help-wanted.yaml (§5)
  - sponsor-asks.yaml
  - feature-names.yaml
- **CI guards (cheap, recommended):**
  - fail the build if a page contains "Pod-class", "Eight Sleep" more than the allowed count (about + features
    only), or an emoji in status labels
  - fail if the feature-names.yaml row count differs from the FEATURES.md table
- The site never shows a temperature that isn't wrapped in `<ModelEstimate>`.

---

## 7. Owner decisions needed (placeholders until then)

1. **Repo URL.** No remote yet. Every "GitHub", issue-template and "Star" link is `{REPO_URL}`.
2. **Sponsor channel.** GitHub Sponsors, Open Collective (gives a transparent ledger, recommended for hardware
   spend) or direct contact. There are no tiers until this is decided.
3. **Contact address** for sponsors, press and safety. The CoC contact is still a placeholder.
4. **Domain** (e.g. `openbed.<tld>`, or a `*.moinsen.dev` subdomain for the preview).
5. **Source fixes:** align the README coldest-water numbers with the kit claims (C1), fix "12 V" in the BOM
   and the README diagram (C2), and replace "Pod-class" in duo-standard.toml and hardware/README.md (C5).
6. **Community channel** (Matrix, Discord or GitHub Discussions), so builders have somewhere to ask before
   they open an issue.
