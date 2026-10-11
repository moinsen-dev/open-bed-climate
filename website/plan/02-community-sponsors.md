# 02: Community, sponsors, legal and trust

> Lens: community, funding/sponsoring, legal and trust. Research date: **2026-10-11**.
> Markers: ✅ verified on the funder's or vendor's own site on that date · ⚠️ partly verified or from a
> third-party source · ❔ not verified, check before relying on it.
> This is planning input, **not legal or tax advice**. Items marked "advice" need a lawyer or Steuerberater.

---

## 0. TL;DR

1. **Fix the name before the site launches.** Eight Sleep holds `POD®`, is filing new `POD` applications and in
   2025–2026 opposed at least six other "…POD" marks for sleep products at the USPTO. "Open Pod" for a two-zone
   water-cooled bed cover is squarely in their lane. A rename now costs a find-and-replace. A rename after launch
   costs the domain, SEO, links and community memory. (Section 4.2)
2. **Two grant windows are open right now:** NLnet (deadline **2026-11-03**, then every odd month) and Prototype
   Fund class 03 (window **2026-10-01 to 2026-11-30**, money from **2027-06-01**). Apply to both. Prototype Fund is
   software-only, so pitch the firmware + Home Assistant stack. (Section 1)
3. **Day one money: GitHub Sponsors** (0 % fee from personal sponsors). Add **Open Collective via Open Source
   Europe** once there are two or more maintainers or real hardware spend to show transparently.
4. **Community home: GitHub Discussions** plus the existing issue templates. No Discord. A Matrix room later, if
   people ask for real-time chat. **Updates: RSS + a GitHub Discussions "Announcements" category**, with listmonk
   (self-hosted, tracking off) once there's demand.
5. **Site legal baseline:** Impressum (§ 5 DDG), a short privacy page, **no cookies, no analytics at launch**,
   self-hosted fonts, no third-party embeds. A disclaimer on every build page: DIY, not certified, not a medical
   device.

---

## 1. Funding channels, ranked

Ranking = fit for *this* project now (pre-prototype, solo maintainer in Germany, strong software, no company)
× effort × time to first euro.

| # | Channel | Fit | Effort | Timing | Status |
|---|---|---|---|---|---|
| 1 | **NLnet** (Restack fund / open call) | Medium-high | Low (short form, English, plain text) | Deadline **2026-11-03 12:00 CET**, then the 3rd of every odd month (next: 2027-01-03) | ✅ |
| 2 | **Prototype Fund** (software, class 03) | Medium-high for the software half | Medium (German application, jury, admin) | Apply **2026-10-01 → 2026-11-30**; funding **2027-06-01 → 2027-11-30** (+ optional second stage) | ✅ |
| 3 | **GitHub Sponsors** | High (where the contributors already are) | Very low | Live in a day | ✅ |
| 4 | **PCB / component sponsors** (AISLER, PCBWay, JLCPCB, Elecrow, NextPCB) | High *once Tier 1 boards exist* | Low per sponsor | When the power board and sensor board reach a first layout | ✅/⚠️ (see below) |
| 5 | **Open Collective** via *Open Source Europe* (Belgium) | Medium (transparency, multi-maintainer, grants to a collective) | Low-medium | After the first prototype, or when a second maintainer joins | ✅ fees, ❔ hardware eligibility |
| 6 | **Prototype Fund Hardware** | Good thematically, but rounds are themed | Medium | Round 3 (2026) was energy-only, €10k, closed 2026-05-01. Next round ❔ | ✅ past round, ❔ next |
| 7 | **Home Assistant / ESPHome ecosystem** | Visibility rather than money | Low | After the first working build | ⚠️ |
| 8 | **Crowd Supply** (hardware crowdfunding) | Good in 12–24 months | High (company, compliance, logistics) | Needs a **late-prototype**; not before a documented, reproduced build | ✅ process |

### 1.1 NLnet: rank 1
- **What:** grants of **€5,000–50,000** for a first grant, can be scaled up later. Cost-recovery rates, not commercial rates. ✅ (nlnet.nl/funding)
- **Status:** NGI Zero Commons Fund is **closed** (final call ended 2026-06-01). NLnet reopened on 2026-09-03 with
  **Restack** (an "Open Internet Stack" fund, first call €500k total) and **CodeSupply**, plus "Other / open call". ✅
- **Fit:** Restack covers "devices used to run and consume [internet commons] in a secure and privacy-friendly
  manner" and "local-first infrastructure". The angle is a **local-first device with an open protocol (OPL) and no
  cloud dependency**, as an alternative to a closed cloud-bound product with a large user base. Medium-high fit.
  The bed itself (water, TECs) is not "internet", so the proposal should centre the **control/hub/protocol/firmware
  stack and its security**, with the hardware as the carrier. If Restack doesn't fit, use the open call.
- **Eligibility:** the outcome must be FOSS/open hardware (✅ already true), with a European dimension (✅ Germany).
- **⚠️ GenAI policy:** NLnet states it is "not interested in AI-generated projects or proposals" and asks for
  answers "in your own words". Prompt logs must be submitted if AI help was used. **Write the proposal yourself**
  and be ready to explain how the code was made. This is a real risk to manage, not a footnote.
- **Budget to ask for (suggestion):** €30–45k over 9–12 months: first hardware bring-up, power board v1, an
  independent safety review, HA/ESPHome integration hardening, a firmware security review (NLnet can provide
  security audits as a service).

### 1.2 Prototype Fund (software): rank 2
- **What:** up to **€47,500** for a single developer (6 months), up to **€95,000** for a team of up to 4 (who must
  form a GbR). Optional second stage, which takes the total to up to €79,167 / €158,000. ✅
- **Window:** class 03 applications **2026-10-01 → 2026-11-30**, selection Dec 2026–Feb 2027, funding starts
  **2027-06-01**. ✅
- **Eligibility:** **software only** (open hardware is explicitly excluded). Applicants must live in Germany and pay
  taxes there, be self-employed or freelance (or be released from their employer for the project's share), and be
  18+. Application in German. ✅
- **Fit:** the repo has a lot of software: the Python reference model, Rust firmware, the ESPHome component, schedules and
  BCG biometrics. Pitch: *"Local-first, open control and sleep-climate software stack for DIY bed climate hardware:
  safety-critical firmware, Home Assistant integration, on-device schedules, privacy-preserving biometrics."*
  The jury looks at social value + user focus. Use the angle of a repairable alternative to subscription-locked devices.
- **Catch:** money only arrives in mid-2027. It funds *time*, not parts.

### 1.3 GitHub Sponsors: rank 3
- **Fees:** **0 %** on sponsorships from personal accounts; **up to 6 %** from organisation accounts (3 % card +
  3 % service; invoiced billing avoids the card part). Up to 10 monthly + 10 one-time tiers. ✅
- **Payout:** Stripe Connect to the maintainer, **or** to a supported fiscal host. "Open Collective Europe" is on
  GitHub's supported fiscal-host list ✅. ❔ It's not verified whether that entry is the same entity as the *Open
  Source Europe ASBL* host recommended in 1.5 (the `opencollective.com/europe` slug now carries that name, while
  oceurope.org presents OCE as a separate foundation). Confirm with GitHub/OSE before planning a "start personal,
  switch payout later" path.
- **Germany:** sponsorship income to an individual is taxable income and needs a tax registration
  (freiberuflich/gewerblich: **advice**). It is *not* a tax-deductible donation for the sponsor.
- **Action:** enable at the org level once the GitHub org exists (named after the final project name).

### 1.4 Component and PCB sponsors: rank 4 (when boards exist)
| Sponsor | Programme | Notes | Status |
|---|---|---|---|
| **AISLER** (Aachen/NL, EU-made) | Open-hardware sponsoring: PCBs + stencils | Asks for a README mention and preferably an "Upload to AISLER" button. EU production, short shipping, fits the European story. **First choice.** | ✅ (2024 programme post; ❔ still active in 2026) |
| **PCBWay** | Non-profit project sponsorship + crowdfunding sponsorship (discounts) | Email sponsor@pcbway.com; 13,800+ projects sponsored | ✅ |
| **JLCPCB / EasyEDA** | Brand Advocate Program (free/discounted PCBs, content-driven); Spark program for EasyEDA designs | Content obligations; the design tool would be KiCad, not EasyEDA | ✅ |
| **Elecrow**, **NextPCB** | PCB/PCBA sponsorship via application form | Smaller, content-driven | ✅ |
| **Distributors** (Mouser, DigiKey, Reichelt) | No public OSHW programme found | Pitch only once there's traffic; Mouser owns Crowd Supply (see 1.8) | ❔ |
| **Mean Well / Peltier / pump vendors** | No programme | Samples for a test build are plausible with a professional ask | ❔ |

**Rule (fits CONTRIBUTING "parts by role, not by brand"):** sponsored parts can be *used in the reference build and
credited*, but they never get a privileged place in `hardware/parts.toml`. Every role keeps several examples. A
sponsor is never the only listed option.

### 1.5 Open Collective: rank 5
- **Open Collective Foundation (US) closed in 2024**. The EU options in 2026: ✅
  - **Open Source Europe ASBL** (Belgium, `opencollective.com/europe`): fiscal host for open-source projects.
    **8 % + Stripe/PayPal fees** online, 10 % for bank transfers, grants and tax-deductible donations. Can sign
    cooperation agreements for **public grants**. Mission is "supporting the open source ecosystem". ❔ Ask whether
    open *hardware* with a physical BOM spend qualifies (likely yes, but confirm).
  - **Open Collective Europe (OCE)** foundation: now framed around grassroots/collective action and regranting
    (123 collectives). Less of a fit for a tech project than Open Source Europe.
  - **German alternative:** a host e.V. such as **Open Source Ecology Germany e.V.** (open-hardware non-profit). ❔
    Whether they fiscally host external projects is not verified. Ask.
- **Why later, not now:** 8–10 % fees and admin overhead pay off only when (a) there are several maintainers who
  spend money, (b) a funder wants to pay an entity rather than a person, or (c) public expense transparency becomes a
  trust feature (it will, once people donate for "test equipment").

### 1.6 Prototype Fund Hardware: watch
- OKF DE programme for open hardware; round 3 (2026) was **themed "OpenEnergy"** (solar, small wind, inverters,
  BMS), **€10k**, application in German, closed **2026-05-01**. ✅ A bed climate system does not fit that theme.
- **Action:** subscribe to the OKF/Prototype Fund newsletter. Apply if a future round has an open or
  "repair/right-to-repair" theme. ❔

### 1.7 Home Assistant / ESPHome ecosystem: visibility, not money
- **Made for ESPHome** / **Works with Home Assistant** are certification programmes for *commercial products* ⚠️.
  They're out of scope until something is sold, and they have their own requirements (❔ check them then).
- **What works now:** a showcase post on the HA community forum, a Device List entry on esphome.io once a build runs,
  the "Community highlights" in the HA blog (❔ submission path), and talks at FOSDEM (Open Hardware / Home
  Automation devrooms) and **Chaos Communication Congress** (Hamburg, late December).
- **Open Home Foundation** (the steward of HA/ESPHome) is a possible later partner or grantor. ❔ No public grant
  programme found.

### 1.8 Crowd Supply: later (12–24 months)
- Still operating, owned by **Mouser**; campaigns live in Sept 2026 (e.g. OpenMote, $166k). ✅
- Requires a **late-prototype** at submission, a prototype sent for photography, and **Mouser supplier onboarding**
  (company documents). Post-campaign stock is sold via Mouser. ✅
- **Hard prerequisites before selling anything in the EU:** a legal entity, CE (LVD + EMC + RED if radio),
  **GPSR** (EU 2023/988) product safety duties, **ElektroG/WEEE** registration (stiftung ear), packaging registration
  (LUCID), and from 2027 the **Cyber Resilience Act** for products with digital elements. ⚠️ (dates and details:
  advice). A mains-adjacent water+heat product is the hard case. Crowd Supply realistically means **modules**
  (sensor board, control board) first, not the whole bed system.

---

## 2. Sponsor tiers and sponsor page

### 2.1 Principles: what sponsors never get
Put these on the sponsor page, word for word, above the tiers:

> **What sponsorship can't buy**
> - **No data.** Open Pod has no cloud and collects nothing. There is no user data to share, now or later.
> - **No say over safety limits.** The limits in SAFETY.md change only through the public safety process.
> - **No exclusivity in the parts catalog.** Parts are listed by role. A sponsor's part is one option, never the only one.
> - **No ads, tracking or telemetry** in firmware, hub, app or docs.
> - **No licence changes.** Everything stays Apache-2.0 / CERN-OHL-S-2.0.
> - **No roadmap control.** Sponsors can tell us what they need; maintainers and contributors decide in public.

### 2.2 Tiers

Individuals (GitHub Sponsors / Open Collective, monthly or one-time):

| Tier | Amount | You get |
|---|---|---|
| **Supporter** | €5 / month | Name on the sponsors page (opt-in), sponsor badge |
| **Builder** | €20 / month | The above + name in the release notes of each hardware revision |
| **Test bench** | €50 / month or €500 one-time | The above + vote in the quarterly "what do we measure next" poll (advisory) |

Organisations:

| Tier | Amount | You get |
|---|---|---|
| **Parts partner** (in-kind) | PCBs, components, samples | Logo in the "Built with parts from" row, a credit in the build log where the part was used, an honest test write-up (good or bad) |
| **Community sponsor** | €250 / month | Small logo on the sponsors page + README |
| **Lab sponsor** | €1,000 / month or a funded line item (e.g. "the thermal camera") | Larger logo, a "this was funded by X" note on the funded result (measurement report, board revision), a mention in the newsletter |
| **Grant / foundation** | Per agreement | Acknowledgement as the funder requires (e.g. NLnet/NGI logo block) |

Keep tiers **few and boring**. No "platinum". No perks that need maintainer time beyond writing credits.

### 2.3 Sponsor page outline (`/sponsor`)
1. **One-sentence ask:** "Open Pod is built in public by volunteers. Your money buys parts, test gear and a safety
   review, not marketing."
2. **Where money goes** (Section 2.4, with a live progress bar per bucket, updated by hand or from Open Collective).
3. **What sponsorship can't buy** (2.1).
4. **Ways to give:** GitHub Sponsors button · Open Collective (once set up) · in-kind parts (mailto form, no
   third-party form tool) · "build one and send a report", which is free and the most valuable thing.
5. **Tiers** (2.2).
6. **Current sponsors and funders** (logos/names, opt-in only).
7. **Transparency:** link to the ledger (Open Collective) or a quarterly "money in / money out" post in the build log.
8. **FAQ:** Is this tax-deductible? (*No, not from an individual maintainer. Maybe via Open Collective; ask.*) ·
   Can I buy a kit? (*Not yet; here's why: safety/compliance.*) · Can my company sponsor a specific feature?
   (*Yes as funding; no as control. See 2.1.*)

### 2.4 Where money goes: first 12 months (proposal)
Rough planning numbers, EUR. BOM figures come from `docs/design/BOM.md`. Equipment and service prices are
order-of-magnitude estimates (❔), not quotes.

| Bucket | What | ~EUR | Why it matters |
|---|---|---|---|
| **1. First prototypes** | 1× Solo Starter (Tier 0), 1× Duo Standard (Tier 0), parts for 1× Duo Reference (Tier 1, ~€1,000 BOM) + spares | 2,500–3,500 | Replaces model estimates with measurements: the most valuable thing the project lacks |
| **2. Test equipment** | Calibrated thermocouple logger, flow meter, power meter / DC clamp meter, thermal camera (entry level), insulation/leak test supplies, a sound level meter | 1,500–2,500 | Makes build reports comparable; lends to builders on request |
| **3. Safety review** | Independent review of SAFETY.md + the electrical design by a qualified electrical engineer (Elektrofachkraft/certified test engineer); a **pre-compliance** EMC/LVD day at a test lab for the Tier 1 power module | 2,000–5,000 | Certification-*oriented* evidence. Not a certification, and the site must say so |
| **4. Boards** | PCB fab + assembly for power board and cover sensor board, 2–3 revisions | 600–1,500 (less with PCB sponsors) | Tier 1 can't exist without it |
| **5. Water mat R&D** | TPU welding samples, medical cooling pads for v0 comparisons | 500–1,500 | The hardest unsolved part (CONTRIBUTING) |
| **6. Builder kits on loan** | 2–3 sets of Tier 1 boards shipped to experienced builders at cost | 500–1,000 | Turns watchers into builders |
| **7. Infra** | Domain, hosting (Cloudflare Pages: €0), listmonk on the existing VM (€0 marginal) | <100 | Keep fixed costs near zero |
| | **Total year 1** | **~7,700–15,100** | |

Display rule: show **buckets with targets and progress**, not a donation total. Post a receipt or photo for every
purchase over €100 in the build log.

---

## 3. Contributor funnel

### 3.1 Where people land: recommendation
| Option | Verdict | Reason |
|---|---|---|
| **GitHub Issues** (templates exist: build report, part substitution, safety concern) | **Primary, for actionable things** | Already structured; templates turn enthusiasm into data |
| **GitHub Discussions** | **Primary, for everything else** | Same login as the code, async, public, indexed by search engines (people searching "DIY bed cooling" find answers), no extra moderation surface. Categories: Announcements · Q&A · Show your build · Ideas · Parts hunting |
| **Matrix room** (bridged) | Later, when ≥ 3 regulars ask for real-time chat | Open, federated, fits local-first. One room, linked from Discussions |
| **Discord** | **No** | Walled and unindexable. Answers vanish, and a "no-cloud" project would depend on a proprietary platform |
| **Forum** (Discourse) | No | Duplicates Discussions, adds hosting + moderation |
| **Newsletter** | Yes, one-way only (Section 5) | For people who won't watch a repo |

Funnel on the site: **Landing → "Pick your role" page** (mirror the CONTRIBUTING table: builder, parts hunter,
electronics/safety, mechanical/textile, firmware, HA, writer). **Each role card has exactly one next action**:
a link to a filtered issue list, a Discussions category or a template.

### 3.2 Good-first-issue strategy
- **Seed 10–15 labelled issues before launch.** An empty `good first issue` list on launch day loses the first wave.
  Candidates straight from STATE.md/CONTRIBUTING:
  - Parts hunting: verify the ❔ parts (GST280A24 / GST90A12 datasheets, a DPDT relay, a certified 50 °C NC cutoff, the leak
    sensor), each one issue. Non-coders can do this.
  - Find a regional source (EU/UK/US) for each role in `parts.toml`, one issue per region.
  - Document the DPS5020 Modbus register map from public sources.
  - Write a new kit TOML variant (e.g. "Solo Quiet") and let the tests judge it.
  - Example Home Assistant dashboard card / automation for the ESPHome entities.
  - Docs: proofread one design doc; start a translation under `docs/i18n/<lang>/`.
  - Code (`help wanted`, not GFI): port `opod.schedule` into the ESPHome component; fan/pump PWM in the firmware.
- **Labels:** `good first issue`, `help wanted`, `needs-measurement`, `needs-hardware`, `safety`, `area:thermal`,
  `area:firmware`, `area:hub`, `area:sensing`, `area:docs`, `area:parts`.
- **Every GFI issue states:** goal, files, how to verify (which test), expected time, and a named maintainer who
  answers within 72 h. An answer within 72 h matters more than the issue count.
- **Safety-limit-touching work is never labelled `good first issue`** (it needs two maintainers per CONTRIBUTING rule 2).

### 3.3 Build-report flow
1. A builder opens a **Build report** issue (template exists).
2. A maintainer labels it `build-report` and checks the safety checkboxes are ticked. If not, they reply with the
   commissioning checklist and don't feature it.
3. Measurements go into a `hardware/builds/<id>.toml` (proposal) via PR, so tests can compare reality to the model.
   *That's where "claims need evidence" pays off.*
4. The site's **Builds gallery** (`/builds`) is generated at build time from merged build TOMLs, not scraped from issues.
5. **Consent:** add a checkbox to `build-report.yml`: *"You may feature my photos and name on the website"*
   (recommendation for the repo owner; not changed here). Without it, show only data, no photos or names.
6. A builder's first featured report earns a "Builder" credit on the contributors wall (3.4).

### 3.4 Recognition
- **all-contributors** spec (`.all-contributorsrc` + bot) so **non-code work counts**: `build`, `research` (parts
  hunting), `review` (safety), `doc`, `translation`, `design`. The site's `/community` page renders that file at
  build time.
- The site fetches **GitHub avatars at build time and self-hosts them**. No hotlinking to GitHub from visitors'
  browsers (privacy, Section 4.1).
- **Release notes** credit everyone by handle; **hardware revisions** carry a "built and measured by" line.
- Optional later: an opt-in **builders map** (country level only, never city).

### 3.5 Before going public (repo hygiene that the site links to)
- `CODE_OF_CONDUCT.md` still has the placeholder `conduct@<project-domain>`. **Set a real address before launch.**
- Add `SECURITY.md` (firmware/hub vulnerability reporting, separate from the public Safety concern template for
  physical hazards).
- `ISSUE_TEMPLATE/config.yml`: set `blank_issues_enabled: false` and add `contact_links` to Discussions Q&A, so
  questions don't land as issues.

---

## 4. Legal and trust checklist for the site

### 4.1 German site law: must-haves
| Item | What | Status / note |
|---|---|---|
| **Impressum** | Required by **§ 5 DDG** (Digitale-Dienste-Gesetz, replaced TMG in May 2024) for "business-like" (*geschäftsmäßige*) services. Assume a sponsor-soliciting project site qualifies. Name, **a postal address that accepts service of process (*ladungsfähige Anschrift*)**, e-mail + a second fast contact channel. Add the editorially responsible person per **§ 18 (2) MStV** for the blog/build log. | ⚠️ A virtual/c-o address is legally contested. Advice before using one instead of a home address |
| **Privacy page** (DSGVO) | Controller, hosting (Cloudflare Pages: server logs, Art. 6(1)(f), US transfer under the EU-US Data Privacy Framework ⚠️), contact e-mail handling, newsletter (if any), rights, supervisory authority | Short, one page |
| **No consent banner** | Under **§ 25 TDDDG** (formerly TTDSG), no non-essential cookies or storage = no banner needed. The design should keep it that way | ✅ by design |
| **Analytics** | **None at launch.** Use GitHub's traffic/referrer stats and the newsletter count. If numbers are needed later: **Plausible (EU-hosted, cookieless)** or self-hosted **GoatCounter**, listed in the privacy page | Recommendation |
| **Fonts** | **Self-host** all fonts (LG München I, 2022: embedding Google Fonts from Google's CDN without consent was ruled unlawful). The site plan must not load from fonts.googleapis.com | Hard rule for the Astro build |
| **Embeds** | No YouTube/Vimeo iframes, no GitHub widgets loaded live. Use **click-to-load** video (thumbnail, then iframe on click) or self-hosted video | Hard rule |
| **External calls** | Zero third-party requests on page load (check with the browser network tab in CI) | Testable acceptance criterion |
| **Licence footer** | "Software & docs Apache-2.0 · Hardware CERN-OHL-S-2.0 · Site content CC BY 4.0 (❔ decide)" | Decide the site-content licence |

### 4.2 Trademark risk: "Open Pod"
**Facts (2026-10-11):**
- Eight Sleep lists **`POD®`**, `EIGHT SLEEP POD®`, `HYPERPOD™` on its IP page, backed by registrations including
  **three EU trade marks (EU 18147731, 18604674, 18643151)**, two UK marks and WIPO/Madrid 1818382 / 1719310 / 1855166. ✅
  **So Eight Sleep has registered trade-mark rights in the EU, where the maintainer lives.** ❔ Which of the three
  EU registrations covers `POD` alone, and in which classes, was not checked (look them up in EUIPO eSearch/TMview).
- USPTO: Eight Sleep has **new `POD` applications** (S# 90861629, 99458663, the latter filed 2025-10-23). ✅
- USPTO TTAB lists Eight Sleep as opposer in 2025–2026 against **SLEEPPOD, KOOLPOD, CLOUD POD, CLAW POD, MRV POD,
  PODAYUDE**. ✅ They are **actively policing "…POD" marks**, including ones weaker than ours.
- Eight Sleep sued a competitor in March 2026 (Eight Sleep v. Orion Longevity, C.D. Cal., patents + other claims). ✅
  So they litigate.
- Our own repo invites the comparison: "Pod-class cooling" in the kit table, "Pod 6 feature parity", `docs/FEATURES.md`
  titled "Pod 6 → Open Pod".

**Assessment (sober):**
- **Same goods** (heated/cooled mattress cover systems with sleep sensing), **dominant shared element "POD"**, and
  "Open" is descriptive (open source), so it doesn't distinguish. That's a classic likelihood-of-confusion setup.
  Using "Pod" while explicitly positioning against the Pod makes it *worse*, not better.
- A non-commercial OSS project is unlikely to face damages. The realistic risks are a **cease-and-desist, a GitHub
  or domain takedown, and a forced rename after the community, SEO and links exist.** Probability of *some* challenge
  once the project gets visible (HN front page, press): **medium-high**. Cost of renaming now: **near zero**
  (repo not public, no domain, no commits).
- **Recommendation:** decide on a new name **before** registering a domain, GitHub org or social handles, and
  before the site goes live. Keep nominative references to the Pod factual and sparse ("comparable to commercial
  bed-cooling covers") and keep the "not affiliated with or endorsed by Eight Sleep" line in the footer.
- **Separate issue, same competitor: patents.** Eight Sleep lists ≥ 6 US patents on the Pod (US 10,792,461, US
  11,666,284, …). Clean-room design protects against *copyright/trade-secret* claims, **not patents**. Private,
  non-commercial building is generally exempt in Germany (§ 11 Nr. 1 PatG) ⚠️, but **selling kits** later needs a
  freedom-to-operate check (advice). Add this to the Crowd Supply prerequisites.

**Alternative names** (*not* a trademark search, just quick availability hints from DNS/GitHub on 2026-10-11; do
an EUIPO/DPMA/USPTO class 9/10/11/20/24 search before choosing). Domain "free" = **no DNS record, likely
unregistered**: a parked domain can also have none, so confirm with a registrar. GitHub "free" = the profile URL
returned 404.

| Name | Idea | .org | .dev | .com | GitHub name | Notes |
|---|---|---|---|---|---|---|
| **Tidebed** | water flowing under you, calm | free | free | taken | free | Short, ownable, no "pod"/"sleep" |
| **Thermoweave** | heat + textile mat | free | free | free | free | Mat-centric, says what it does |
| **Kelvinbed** | temperature unit, engineering feel | free | free | free | taken (user) | Use `kelvinbed-project` org |
| **Open Bed Climate** (OBC) | purely descriptive | free | free | free | free | Hard to trademark, which also means hard to *be attacked over*; weak brand |
| **Bedclimate** | descriptive | free | free | taken | free | Same trade-off as above |

No renames are made in this plan; this is input for the maintainer's decision.

### 4.3 Disclaimer wording (site-wide + on every build page)
Short footer line:
> Open Pod is an experimental DIY project. Nothing here is certified, sold or supported as a product. Not a
> medical device. Not affiliated with Eight Sleep.

Build/kit pages (box above the first instruction, linking to SAFETY.md):
> **Experimental hardware. Build at your own risk.** This design combines water, several hundred watts and a
> sleeping person. It is **not certified** (no CE marking, no safety approval) and is published for education and
> experimentation. Have the electrical part checked by a qualified person before you sleep on a build, and complete
> the commissioning checklist first. Mains-side work on Tier 1 power modules must be done by a qualified electrician.
> The information is provided "as is", without warranty, under the project licences.

Biometrics/sleep pages:
> Heart rate, breathing and sleep data from Open Pod are **estimates for personal interest**. Open Pod is **not a
> medical device** and is not intended to diagnose, treat, monitor or prevent any disease or condition. Talk to a
> doctor about health concerns.

Wording rules for the whole site: never say "safe", "certified", "clinically proven", "improves sleep"
or "medical". Say "designed with independent hardware safety limits", "measured", "estimated". This also keeps the
project clear of EU MDR "intended purpose" questions ⚠️ (advice if biometric features grow).

German liability note (advice): German law limits how far a disclaimer can exclude liability for injury
(*Haftungsausschluss* is not a shield for gross negligence or bodily harm). The real protection is the safety
architecture, the commissioning checklist and honest wording, so **SAFETY.md must stay the most prominent link on
every build page**.

---

## 5. Newsletter and updates without tracking

| Option | Data | Effort | Verdict |
|---|---|---|---|
| **RSS/Atom feed** of the site's build log (Astro `@astrojs/rss`) | None | Minutes | **Launch with this** |
| **GitHub Discussions "Announcements"** + "Watch → Releases" | GitHub's own | None | **Launch with this** |
| **listmonk** (AGPLv3, self-hosted, v6.2.0 June 2026) on the existing Hetzner VM; tracking pixels and link tracking switched off, double opt-in, one-click unsubscribe | E-mail only, on your own server in Germany | ~1 h setup + SMTP (e.g. the existing transactional mail provider) | **Add when ~100 people ask for e-mail updates** ✅ |
| **Buttondown** with analytics and link tracking off | E-mail, US processor (needs a DPA + privacy-page entry) | Minutes | Acceptable fallback if self-hosting is unwanted ✅ |
| Substack, Mailchimp, beehiiv | Tracking by default, ads/upsells | — | **No** |

Cadence: **one update per milestone, not per calendar** (first bring-up, first cold night, board v1, grant decisions).
Each update = one build-log post, and RSS + e-mail send the same text. The sign-up form is a plain HTML form posting
to listmonk (no third-party JS), with the privacy page linked next to the button.

---

## 6. Timeline (what to do when)

| When | Action |
|---|---|
| **Before site launch** | Decide the name (4.2) → domain → GitHub org. Set the CoC contact. Add SECURITY.md. Seed 10–15 GFIs. Enable Discussions. Impressum + privacy page. |
| **By 2026-11-03** | NLnet proposal (Restack or open call), written by the maintainer in their own words. |
| **By 2026-11-30** | Prototype Fund class 03 application (software stack, in German). |
| **Launch week** | GitHub Sponsors live; `/sponsor` page with the buckets; first build-log post; RSS. |
| **First Tier 1 layout** | AISLER + PCBWay sponsorship requests. |
| **First prototype measured** | HA forum showcase, FOSDEM CfP (opens ~autumn ❔), Open Collective via Open Source Europe if spending starts. |
| **~100 e-mail requests** | listmonk. |
| **12–24 months, reproduced builds** | Decide on a legal entity + compliance path → Crowd Supply for modules. |

---

## Sources (accessed 2026-10-11)
- NLnet funding, calls, Restack, CodeSupply, GenAI policy: https://nlnet.nl/funding.html · https://nlnet.nl/propose/ ·
  https://nlnet.nl/restack/ · https://nlnet.nl/news/2026/20260903-call.html · https://nlnet.nl/commonsfund
- Prototype Fund: https://www.prototypefund.de/en/funding · https://www.prototypefund.de/en/faq · https://www.prototypefund.de/
- Prototype Fund Hardware: https://hardware.prototypefund.de/bewerbung · https://hardware.prototypefund.de/bewerbung/bewerbung-einreichen
- GitHub Sponsors fees and fiscal hosts: https://docs.github.com/en/billing/concepts/third-party-payments/github-sponsors ·
  https://github.com/github/docs/blob/main/content/sponsors/receiving-sponsorships-through-github-sponsors/using-a-fiscal-host-to-receive-github-sponsors-payouts.md
- Open Source Europe / OCE: https://opencollective.com/europe/apply · https://www.oceurope.org/
- PCB sponsors: https://community.aisler.net/t/sponsoring-for-open-hardware-projects/3786 · https://www.pcbway.com/project/sponsor/publish.aspx ·
  https://jlcpcb.com/help/article/get-free-pcbs-get-paid-to-build-join-the-jlcpcb-brand-advocate-program · https://www.elecrow.com/sponsorships.html · https://www.nextpcb.com/creator-support
- Crowd Supply: https://www.crowdsupply.com/guide/the-life-cycle-of-a-crowd-supply-campaign · https://www.crowdsupply.com/
- Eight Sleep IP/trademarks: https://www.eightsleep.com/ch-de/intellectual-property · https://ttabvue.uspto.gov/ttabvue/v?pnam=Eight%20Sleep%20Inc.%20%20 ·
  https://www.trademarkia.com/pod-99458663 · https://dockets.justia.com/docket/california/cacdce/2:2026cv02460/1009856
- Newsletter: https://listmonk.app/ · https://buttondown.com/features/privacy · https://plausible.io/data-policy
