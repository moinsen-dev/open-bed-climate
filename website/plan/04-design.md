# 04 — Visual design and UX

Lens: visual design and UX for the Open Pod website (Astro, static, English).
Token source of truth: [`/DESIGN.md`](../../DESIGN.md) (lint-clean with `npx @google/design.md lint DESIGN.md`,
0 errors / 0 warnings as of 2026-10-11). This document gives the rationale, the component specs and the wireframes.

---

## 1. Direction: "Thermal Night"

**One idea:** a dark, quiet night-sky page where **the only color is temperature**. Cold cyan and warm amber are mapped
to the system's real setpoint range (13–43 °C), so every accent carries meaning. All illustration is **hairline
engineering schematics**: the water loop, the hub, an exploded kit. The schematic style is the illustration language
of Thermal Night, not a second aesthetic.

Why this and not the alternatives:

| Option | For | Against | Verdict |
|---|---|---|---|
| **Thermal Night** (chosen) | Sleep-calm by default (dark, low chroma); the color system *is* the product (temperature control); hairline schematics read as "open, buildable, inspectable"; looks premium enough for sponsors | Dark sites can feel generic "dev tool": countered by the warm amber CTA, a humane display font and real data in the hero | **Yes** |
| Pure blueprint (blue paper, white lines) | Strong maker signal | Cold, busy, shouts "CAD" rather than "sleep"; one-hue, so the temperature story is lost | No, but its line style is borrowed for the diagrams |
| Soft wellness (pastels, rounded, photos of beds) | Consumer-friendly | Needs product photos we don't have; looks like a commercial pod brand (forbidden by our constraints); doesn't recruit engineers | No |

**Honesty principle.** The project is in design phase: no physical build has been measured. Schematics show *what is
designed*; a glossy render would imply a finished product. Every visual that shows numbers labels them as **model
estimates**, and status chips show `done`, `next` or `help wanted`, never "available" or "shipping".

**Feel words:** calm, precise, warm-hearted, inspectable.

---

## 2. Typography

All OFL-licensed, self-hosted through Fontsource (`@fontsource-variable/*`), subset to Latin, `font-display: swap`,
preload only the display woff2 used above the fold.

| Role | Family | Weights | Use |
|---|---|---|---|
| Display / headlines | **Bricolage Grotesque** (variable, opsz) | 600, 700 | H1–H3, hero, card titles |
| Body / UI | **Inter** (variable) | 400, 600 | prose, nav, buttons, tables |
| Readouts / labels / code | **JetBrains Mono** (variable) | 400, 600 | every °C, W, L/min, part id, eyebrows, status chips, code |

Scale (rem, root 16px; fluid with `clamp()` between 360px and 1200px viewports):

| Token | Mobile | Desktop | Line height |
|---|---|---|---|
| `display` | 2.75 | 4.5 | 1.0 |
| `headline-lg` | 2.0 | 2.75 | 1.08 |
| `headline-md` | 1.5 | 1.75 | 1.2 |
| `headline-sm` | 1.125 | 1.25 | 1.3 |
| `body-lg` | 1.0625 | 1.1875 | 1.6 |
| `body-md` | 1.0 | 1.0 | 1.6 |
| `body-sm` | 0.875 | 0.875 | 1.5 |
| `label-caps` (mono, uppercase, 0.08em) | 0.75 | 0.75 | 1.3 |
| `readout-lg` (mono, tnum, slashed zero) | 2.25 | 3.0 | 1.0 |

Rules: max 3 families per page, max 2 weights per family; prose measure 60–72ch; numbers always in mono with
`font-feature-settings: "tnum" 1, "zero" 1` so values do not jitter while animating.

---

## 3. Color tokens

Night is the default theme (it is a sleep product; it also flatters the temperature colors). Dawn is the light theme,
selected by `prefers-color-scheme: light` or a header toggle (stored in `localStorage`, wrapped in try/catch).

### Night (default)

| Token | Hex | Role |
|---|---|---|
| `canvas` | `#070B16` | page background |
| `surface` | `#0E1528` | cards, callouts |
| `surface-raised` | `#16203B` | kit cards, code, hover state |
| `hairline` | `#2A3A63` | decorative rules, diagram strokes (not control borders) |
| `border-strong` | `#56688F` | inputs, secondary button outline (≥ 3:1) |
| `ink` | `#E9EEF7` | primary text |
| `ink-muted` | `#A3B0C8` | secondary text |
| `primary` (warm amber) | `#FFB547` | primary CTA fill, help-wanted chip |
| `primary-hover` | `#FFC56E` | CTA hover |
| `cold` | `#5CD3F0` | links, focus ring, live readouts |
| `success` / `warning` / `danger` | `#5BD89A` / `#FFD166` / `#FF7A7A` | status; warning = safety only |

### Temperature scale (diverging, cold → warm)

| Token | Hex | Anchor |
|---|---|---|
| `temp-13` | `#4C9BFF` | 13 °C, coldest setpoint |
| `temp-20` | `#5CD3F0` | ~20 °C, deep-sleep default |
| `temp-28` | `#D8E4EC` | ~28 °C, neutral / skin-neutral |
| `temp-36` | `#FFB547` | ~36 °C |
| `temp-43` | `#FF8F4A` | 43 °C, warm safety cap |

Mapping function (one helper, `tempColor(c)`): linear interpolation in OKLCH between the five stops, clamped to
13–43 °C. Blue-to-orange is distinguishable for the common red/green color-vision deficiencies, but color is still
**never** the only carrier: every colored value is printed as a number.

### Dawn (light)

| Token | Hex | Role |
|---|---|---|
| `dawn-canvas` | `#F5F3ED` | paper background |
| `dawn-surface` | `#FFFFFF` | cards |
| `dawn-surface-raised` | `#ECEFF5` | kit cards, code |
| `dawn-border-strong` | `#6B778E` | control borders |
| `dawn-ink` / `dawn-ink-muted` | `#0B1222` / `#4A5670` | text |
| `dawn-cold` / `dawn-warm` | `#0A6E8C` / `#9C5200` | temperature text **and** curve strokes on light |
| `dawn-link` | `#0B5FA5` | links, focus ring |
| `dawn-success` / `dawn-warning` / `dawn-danger` | `#1C7A4A` / `#8A5B00` / `#B42318` | status |

On Dawn, the primary button keeps the amber `#FFB547` fill with `dawn-ink` text. The mid-tone temperature stops are
too light for strokes on paper (≈ 2.5:1), so Dawn graphics use `dawn-cold` / `dawn-warm` for lines and keep the
light stops only as fills behind labelled values.

---

## 4. Motion

Principles:
1. **Motion = time passing in a night.** The only continuous animation is the hero curve; everything else is a
   one-shot reveal.
2. **Slow and smooth:** 200 ms UI feedback, 400–600 ms reveals, `cubic-bezier(0.2, 0.7, 0.2, 1)`. No bounces, no
   parallax, no scroll-jacking.
3. **Reduced motion:** under `prefers-reduced-motion: reduce`, the hero shows a static frame at minute 120
   (20 °C, deep sleep), reveals become instant, gradient shimmer is off.
4. **Pause control:** the hero animation loops longer than 5 s, so it has a visible pause/play button
   (WCAG 2.2.2). It also pauses when off-screen (`IntersectionObserver`) and when the tab is hidden.
5. **No layout shift:** animated elements have fixed boxes; numbers use tabular figures.
6. **JS optional:** the hero is server-rendered SVG with a static frame; a small island (< 6 KB) animates it.

---

## 5. Illustration strategy (no product photos)

All illustrations are inline or file SVG, authored by hand or in a vector tool, sharing one style:

- 1.5px strokes in `ink-muted` (Night) or `dawn-ink-muted` (Dawn); construction lines in `hairline`, dashed 2/4.
- Square corners, orthographic or 30° isometric only. No shading, no gradients, except **water paths**, which carry
  the temperature color, and the hero glow.
- Callout labels in `label-caps` mono with thin leader lines, like a datasheet drawing.
- Every SVG has `role="img"`, a `<title>` and a `<desc>`; complex diagrams also get a text equivalent below them.
- `currentColor` and CSS custom properties for strokes, so both themes come from one file.

Set:
| # | Illustration | Where | Content |
|---|---|---|---|
| I1 | **Bed outline** (top view, 2 zones) | hero | mattress outline, water mat channel serpentine per side, umbilical to the hub |
| I2 | **Water loop** (animated flow on hover/scroll, static under reduced motion) | home "How it works" | mat → lines → pump → cold plate/TEC → heatsink + fan → reservoir → back; cold and warm water legs colored |
| I3 | **Exploded kit** (isometric) | kits overview | hub enclosure lid lifted: PSU, Pico 2, ESP32, TEC stacks on cold plates, pump, reservoir, quick-disconnects |
| I4 | **Safety layers** (concentric rings) | home safety band, SAFETY page | hardware cutoffs → MCU clamp 13–43 °C → hub requests only |
| I5 | **Module map** | kits, docs | the module diagram from `hardware/README.md` redrawn in house style |
| I6 | **Zone glyphs** | kit cards | 1-zone / 2-zone bed icons, sensing icons (load cell, pneumatic, piezo grid) |
| I7 | **Contributor role icons** | get-involved | builder, parts hunter, electronics, textile, firmware, Home Assistant, writer: 24px line icons, one shared stroke set |

No vendor products, no logos, no stock bedrooms. Third-party logos (Home Assistant, Raspberry Pi etc.) appear only as
text names, never as marks.

---

## 6. Signature hero: "One night, live"

A top-view bed outline (I1) with a soft temperature glow inside the mat area, and a mono readout that plays through
the **real default night program** from `software/obc/src/obc/schedule.py:61`:

```
DEFAULT = Schedule(points=((0, 24.0), (30, 21.0), (120, 20.0), (300, 23.0), (420, 25.0)))
wake_ramp_min = 30, wake_target_c = 32.0
```

Hero assumption: bedtime 23:00, wake 07:00 (480 min). The curve holds 25 °C after minute 420, the wake ramp runs
from minute 450 to 480 (25 → 32 °C). Keyframes:

| Clock | Min | °C | Phase label |
|---|---|---|---|
| 23:00 | 0 | 24.0 | Bedtime |
| 23:30 | 30 | 21.0 | Falling asleep |
| 01:00 | 120 | 20.0 | Deep sleep (coolest) |
| 04:00 | 300 | 23.0 | Easing warmer |
| 06:00 | 420 | 25.0 | Late sleep |
| 06:30 | 450 | 25.0 | Wake ramp starts |
| 07:00 | 480 | 32.0 | Wake |

Behaviour:
- One loop = 16 s (2 s per night hour), ease-linear in time, interpolated exactly like `Schedule.setpoint`.
- Below the bed, a thin **night strip**: the curve drawn as a 1.5px line on a 13–43 °C axis, a moving playhead,
  clock ticks every 2 h. The glow color = `tempColor(current °C)`, readout shows `20.4 °C`, clock and phase label.
- Two-zone variant: left side runs the default, right side runs the same curve offset +1.5 °C, so visitors see
  "each side its own climate" without a word of copy.
- Static frame / no-JS / reduced motion: minute 120, 20.0 °C, "Deep sleep", full curve drawn.
- Accessibility: the SVG is `aria-hidden`, the readout region is not live (no `aria-live` chatter); a visually
  hidden sentence describes the program: "Default night program: 24 °C at bedtime, 20 °C in deep sleep, warming to
  32 °C at wake." Pause/play button bottom-right, 44×44 px.
- Caption under it: *"The default night program, from the reference code. Model data, not a measurement."*

The same widget (`ScheduleCurve`) is reused in an interactive form on the software/feature page: drag the 5 points,
read the clamped values (13–43 °C), copy the result as TOML/YAML.

---

## 7. Component inventory

| Component | Purpose | Key specs |
|---|---|---|
| `SiteHeader` | logo wordmark, nav (Kits, How it works, Get involved, Sponsor, GitHub), theme toggle | sticky, 64px; becomes solid `canvas` at 92% + backdrop blur; must never cover focused elements (`scroll-padding-top: 80px`, WCAG 2.4.11) |
| `Wordmark` | "Open Pod" in Bricolage 700 + a small two-zone glyph whose halves are cold/warm | SVG, no other brand's shapes |
| `Hero` | headline, lead, 2 CTAs, `ScheduleCurve` hero mode | CTAs: primary "Build one" → kits, secondary "Contribute" → get-involved |
| `ScheduleCurve` | signature widget (hero + interactive mode) | see §6 |
| `PillarCard` ×4 | Open · Local-first · Standard parts · Adaptable kits | icon (line), title `headline-sm`, 2 lines body, link |
| `SafetyCallout` | "Water + several hundred watts + a sleeping person. Nothing here is certified." → SAFETY.md | warning left rule 4px, warning icon + text; required on home + every kit page |
| `StatusTimeline` | design-phase honesty: rows from README status table | vertical on mobile, horizontal steps ≥ md; chips `done` (success), `next` (cold), `help wanted` (amber, pulses once on reveal) |
| `WaterLoopDiagram` | I2 with step captions | numbered hotspots, text list below as equivalent |
| `KitCard` ×3 | Solo Starter, Duo Standard, Duo Reference | zone glyph, tier chip, mono readouts "coldest ~21.5 °C*" (color from temp scale) and "warms to 43 °C", "best for" line, link to TOML + kit page; footnote "*model estimate, 25 °C room" |
| `KitCompareTable` | zones, TEC/zone, sensing, PSUs, coldest water, tier | sticky first column on mobile, horizontal scroll inside the table only |
| `PartsTable` | role → requirement → example parts | mono part ids, role filter chips, safety-relevant roles marked with icon + text "safety" |
| `CodeSnippet` | `uv run pytest -q`, `cargo test` | copy button (aria-label), mono, `surface-raised` |
| `RoleCard` | contributor roles (builder, parts hunter, electronics, textile, firmware, HA, writer) | icon, one-line "you could…", "first issue" link |
| `FirstBuildBand` | the #1 ask: first physical build + measurements | full-width CTA band, amber primary button → build-report issue template |
| `CtaBand` | generic closing band | headline + 1 primary + 1 secondary |
| `SponsorTierCard` | tiers (e.g. Backer, Builder, Lab) | name, what it funds (parts for test builds, PCB runs, measurement gear), what sponsors get (name on site/README, build-report shout-outs), CTA; the middle tier gets a 1px amber outline, no "most popular" badge |
| `SponsorWall` | names as text only (no third-party logos until a sponsor contract allows it) | grid of mono names |
| `LicenseBadges` | Apache-2.0 / CERN-OHL-S-2.0 | text chips, not shields-style imitation |
| `SiteFooter` | links, licenses, non-affiliation line ("Open Pod is not affiliated with or endorsed by any commercial bed-climate vendor."), safety link, repo link | `surface`, body-sm |

States for all interactive components: default, hover (surface → surface-raised), focus-visible (2px cold ring,
2px offset), active, disabled (opacity .5 + `aria-disabled`, no color-only meaning).

---

## 8. Page wireframes

### 8.1 Home `/`

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ◐ Open Pod      Kits  How it works  Get involved  Sponsor   GitHub  [☾/☀]│ sticky
├──────────────────────────────────────────────────────────────────────────┤
│ OPEN-SOURCE BED CLIMATE · DESIGN PHASE                     (eyebrow)     │
│                                                                          │
│ Your bed, at the right               ┌──────────────── bed (top) ──────┐ │
│ temperature. All night.              │ ░░▒▒▓▓ glow L ▓▓▒▒│▒▒▓ glow R ▒░ │ │
│ Built by you.                        │ ~~~~ channels ~~~~│~~~~~~~~~~~~ │ │
│                                      └────────────┬──────┴─────────────┘ │
│ Water-cooled and heated mat, local     umbilical  └──[ hub ]             │
│ control, no cloud, standard parts.   01:00  DEEP SLEEP   20.0 °C         │
│                                      13 ─────╲___________/‾‾‾‾╱── 43     │
│ [ Build one → ]  ( Contribute )      23:00   ▲playhead        07:00 [❚❚] │
│                                      "Default night program. Model data."│
├──────────────────────────────────────────────────────────────────────────┤
│ [Open]          [Local-first]      [Standard parts]    [Adaptable kits]  │ PillarCard ×4
├──────────────────────────────────────────────────────────────────────────┤
│ ⚠ Water + several hundred watts + a sleeping person. Nothing is          │ SafetyCallout
│   certified. Read SAFETY.md before you build →                           │
├──────────────────────────────────────────────────────────────────────────┤
│ HOW IT WORKS                                                             │
│  mat ═cold═▶ pump ─▶ cold plate/TEC ─▶ heatsink+fan     1 Mat  2 Pump    │ WaterLoopDiagram
│   ▲                        │                            3 TEC  4 MCU     │
│   ╚════════warm════ reservoir ◀┘                        5 Hub ⇄ HA       │
├──────────────────────────────────────────────────────────────────────────┤
│ PICK A KIT                                                               │
│ ┌ Solo Starter ┐  ┌ Duo Standard ┐  ┌ Duo Reference ┐                    │ KitCard ×3
│ │ ▭ 1 zone T0  │  │ ▭▭ 2 zone T0 │  │ ▭▭ 2 zone T1  │                    │
│ │ ~21.5 °C*    │  │ ~18.6 °C*    │  │ ~18.3 °C*     │                    │
│ │ → 43 °C      │  │ → 43 °C      │  │ → 43 °C       │                    │
│ └──────────────┘  └──────────────┘  └───────────────┘   * model estimate │
├──────────────────────────────────────────────────────────────────────────┤
│ WHERE WE ARE                                                             │
│ ✓ Feature parity ✓ System design ✓ Kits ✓ Reference sw ✓ Firmware        │ StatusTimeline
│ ✓ Hub/HA  ●── First physical build  [HELP WANTED]                        │
├──────────────────────────────────────────────────────────────────────────┤
│ ███ Be the first to build one. Post a build report. [ Start a build → ]  │ FirstBuildBand
├──────────────────────────────────────────────────────────────────────────┤
│ Builders · Electronics · Textile · Firmware · HA · Writers  → Get involved│ RoleCard strip
│ Support the first prototypes → Sponsor                                   │ CtaBand
├──────────────────────────────────────────────────────────────────────────┤
│ footer: docs · safety · licenses · repo · non-affiliation note           │
└──────────────────────────────────────────────────────────────────────────┘
```
Mobile: hero stacks (text → widget → CTAs full width), pillars 1 column, kit cards horizontal snap carousel with
visible next-card peek **and** a "compare all kits" link (no carousel-only content).

### 8.2 Kits `/kits` (+ `/kits/[slug]`)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ KITS                                                                     │
│ Start from a kit. Change anything. The tests check your claims.          │
│ [ I3 exploded kit illustration, hairline isometric, labelled parts ]     │
├──────────────────────────────────────────────────────────────────────────┤
│ ⚠ Safety callout → SAFETY.md                                             │
├──────────────────────────────────────────────────────────────────────────┤
│ Filter: (1 zone) (2 zones) (Tier 0) (Tier 1)                             │
│ ┌ KitCard ┐ ┌ KitCard ┐ ┌ KitCard ┐                                       │
├──────────────────────────────────────────────────────────────────────────┤
│ COMPARE                                                                  │
│ │ Kit      │Tier│Zones│TEC/z│Sensing   │PSUs              │Coldest*│     │ KitCompareTable
│ │ Solo St. │ 0  │ 1   │ 3   │load cells│24V 280W+12V 90W  │~21.5 °C│     │
│ │ Duo Std. │ 0  │ 2   │ 4   │pneumatic │2×24V 280W+12V 90W│~18.6 °C│     │
│ │ Duo Ref. │ 1  │ 2   │ 4   │piezo grid│24V 750W module   │~18.3 °C│     │
├──────────────────────────────────────────────────────────────────────────┤
│ TIERS: Tier 0 modules only · Tier 1 reference PCBs  (two short cards)    │
│ MODULE MAP (I5)                                                          │
│ BRING YOUR OWN KIT: copy a TOML, edit, run tests   [code snippet ⧉]      │
└──────────────────────────────────────────────────────────────────────────┘
Kit detail /kits/solo-starter:
  breadcrumb · title + chips (Tier 0, 1 zone) · readouts (coldest*, warm cap) ·
  SafetyCallout · "Who it's for" · PartsTable (roles, safety-relevant marked) ·
  "Open the TOML on GitHub" · "Post a build report" CTA
```

### 8.3 Get involved `/get-involved`

```
┌──────────────────────────────────────────────────────────────────────────┐
│ GET INVOLVED                                                             │
│ There is a place for you. The most valuable thing right now:             │
│ ███ The first physical build + measurements   [ Start a build → ]        │ FirstBuildBand
├──────────────────────────────────────────────────────────────────────────┤
│ ┌ Builder ┐ ┌ Parts hunter ┐ ┌ Electronics ┐ ┌ Textile ┐                  │ RoleCard grid
│ ┌ Firmware (Rust) ┐ ┌ Home Assistant ┐ ┌ Writer ┐                         │ (3 / 2 / 1 cols)
│   each: what you'd do · skills · "good first issue" link                 │
├──────────────────────────────────────────────────────────────────────────┤
│ RUN IT IN 2 MINUTES (no hardware needed)                                 │
│ $ cd software/obc && uv run pytest -q          [⧉]                      │ CodeSnippet ×2
│ $ cd firmware && cargo test                     [⧉]                      │
├──────────────────────────────────────────────────────────────────────────┤
│ HOW WE WORK: CONTRIBUTING · Code of Conduct · open decisions list        │
│ StatusTimeline (compact)                                                 │
└──────────────────────────────────────────────────────────────────────────┘
```

### 8.4 Sponsor `/sponsor`

```
┌──────────────────────────────────────────────────────────────────────────┐
│ SPONSOR                                                                  │
│ Fund the first prototypes of an open, local-first bed climate system.    │
│ What money buys (mono list): test builds · PCB runs · measurement gear   │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌ Backer ─────┐  ┌ Builder ─────┐  ┌ Lab ─────────┐                     │ SponsorTierCard ×3
│ │ funds …     │  │ (amber 1px)  │  │ funds …      │                     │
│ │ you get …   │  │ funds …      │  │ you get …    │                     │
│ │ [ Sponsor ] │  │ [ Sponsor ]  │  │ [ Talk to us]│                     │
│ └─────────────┘  └──────────────┘  └──────────────┘                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Hardware companies: donate parts → we publish measured results openly    │
│ TRANSPARENCY: where money went (table, updated per build)                │
│ SPONSOR WALL (text names)                                                │
│ FAQ (accordion: licenses, no ads, no data, independence)                 │
└──────────────────────────────────────────────────────────────────────────┘
```
Tier names and amounts are placeholders for the community/content plan.

---

## 9. Accessibility (WCAG 2.2 AA)

Measured contrast (WCAG relative luminance, computed 2026-10-11):

**Night**
| Foreground | Background | Ratio | Use | Pass |
|---|---|---|---|---|
| ink `#E9EEF7` | canvas `#070B16` | 16.88 | body | AA/AAA |
| ink | surface `#0E1528` | 15.60 | cards | AA/AAA |
| ink | surface-raised `#16203B` | 13.83 | kit cards | AA/AAA |
| ink-muted `#A3B0C8` | canvas / surface / raised | 8.99 / 8.30 / 7.36 | secondary text | AA/AAA |
| cold `#5CD3F0` | canvas / surface | 11.26 / 10.40 | links, readouts | AA |
| primary `#FFB547` | canvas / surface | 11.19 / 10.33 | amber text, chips | AA |
| canvas text on primary fill | — | 11.19 | primary button | AA |
| canvas text on primary-hover `#FFC56E` | — | 12.60 | button hover | AA |
| temp-13 `#4C9BFF` | surface-raised | 5.71 | coldest readout | AA |
| temp-43 `#FF8F4A` | surface-raised | 7.12 | warm readout | AA |
| temp-28 `#D8E4EC` | canvas | 15.19 | neutral curve label | AA |
| success / warning / danger | surface | 10.15 / 12.59 / 7.19 | status | AA |
| border-strong `#56688F` | canvas / surface | 3.53 / 3.26 | control borders (non-text ≥ 3:1) | AA |
| hairline `#2A3A63` | canvas | 1.76 | decorative only, never sole boundary | n/a |

**Dawn**
| Foreground | Background | Ratio | Use | Pass |
|---|---|---|---|---|
| dawn-ink `#0B1222` | canvas `#F5F3ED` / surface `#FFF` | 16.84 / 18.69 | body | AA/AAA |
| dawn-ink-muted `#4A5670` | canvas / surface / raised | 6.63 / 7.35 / 6.38 | secondary text | AA |
| dawn-link `#0B5FA5` | canvas / surface | 5.92 / 6.57 | links, focus | AA |
| dawn-cold `#0A6E8C` | canvas / surface / raised | 5.23 / 5.80 / 5.03 | cold text + strokes | AA |
| dawn-warm `#9C5200` | canvas / surface / raised | 5.23 / 5.80 / 5.04 | warm text + strokes | AA |
| dawn-ink on primary `#FFB547` | — | 10.64 | primary button | AA |
| dawn-success / warning / danger | surface | 5.34 / 5.87 / 6.57 | status | AA |
| dawn-border-strong `#6B778E` | canvas / surface | 4.07 / 4.51 | control borders | AA |
| mid-tone `#2FA8C8` / `#E08A12` | dawn-canvas | 2.50 / 2.42 | **not allowed** as text or sole stroke on Dawn | fail → replaced |

Further rules:
- **1.4.1 Use of color:** temperature always printed in °C; status chips carry text; safety-relevant parts carry an
  icon and the word "safety".
- **2.2.2 Pause, stop, hide:** hero pause button; animation stops off-screen and under reduced motion.
- **2.4.7 / 2.4.11 / 2.4.13 Focus:** 2px solid ring + 2px offset in `cold`/`dawn-link` (≥ 3:1 against adjacent
  colors), `scroll-padding-top` clears the sticky header.
- **2.5.8 Target size:** every target ≥ 24×24 px; buttons 48px tall, icon buttons 44×44.
- **1.4.10 Reflow / 1.4.12 Text spacing:** works at 320px and 200% zoom; tables scroll inside their own container.
- **Landmarks and order:** one `h1` per page, skip link, `header/nav/main/footer`, diagrams with `title`+`desc`
  and a text alternative.
- **Forms** (newsletter/contact, if any): visible labels, errors in text plus `aria-describedby`.
- Check in CI: `npx @google/design.md lint DESIGN.md` (token contrast) + axe/pa11y on built pages + Lighthouse a11y
  ≥ 95.

---

## 10. Responsive breakpoints

| Name | Min width | Container padding | Grid | Notes |
|---|---|---|---|---|
| base | 0 | 16px | 1 col | hero stacked, CTAs full width, nav in a disclosure menu |
| `sm` | 640px | 24px | 2 col | pillar and role cards 2-up |
| `md` | 900px | 32px | 3 col / hero 2 col (text 5 : widget 7) | nav inline, kit cards 3-up, timeline horizontal |
| `lg` | 1200px | 40px | 12-col, max-width 1200px | hero widget can bleed to the right edge |

Fluid type via `clamp()` between 360px and 1200px. Images/diagrams are SVG, so one asset serves all widths; the
exploded kit (I3) has a simplified mobile variant with fewer labels.

---

## 11. Implementation notes for the tech plan

- Tokens: `npx @google/design.md export --format css-vars DESIGN.md` → `src/styles/tokens.css`; Night values on
  `:root`, Dawn values under `@media (prefers-color-scheme: light)` guarded by `:root:not([data-theme="dark"])`, and
  under `:root[data-theme="light"]`. `body` always gets an explicit background.
- Fonts: `@fontsource-variable/bricolage-grotesque`, `@fontsource-variable/inter`,
  `@fontsource-variable/jetbrains-mono`.
- `ScheduleCurve`: an Astro component rendering the static SVG + a tiny vanilla-TS island for animation; the
  schedule points live in one JSON file (`src/data/default-schedule.json`) generated from or checked against
  `software/obc/src/obc/schedule.py` so the site never drifts from the code.
- Kit numbers come from `hardware/kits/*.toml` at build time, not hand-typed copy.
- Performance budget: < 100 KB JS total, LCP < 2.0 s on 4G, CLS < 0.05.
