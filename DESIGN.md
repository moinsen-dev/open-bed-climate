---
version: alpha
name: Open Bed Climate — Thermal Night
description: Calm night-sky canvas, temperature as the only accent (cold cyan to warm amber, mapped to the real 13–43 °C setpoint range), hairline schematic drawings instead of product photos.
colors:
  # Night theme (default)
  canvas: "#070B16"
  surface: "#0E1528"
  surface-raised: "#16203B"
  hairline: "#2A3A63"
  border-strong: "#56688F"
  ink: "#E9EEF7"
  ink-muted: "#A3B0C8"
  cold: "#5CD3F0"
  primary: "#FFB547"   # warm amber, the action color
  primary-hover: "#FFC56E"
  success: "#5BD89A"
  warning: "#FFD166"
  danger: "#FF7A7A"
  # Temperature scale (shared, graphics + labels on night surfaces)
  temp-13: "#4C9BFF"
  temp-20: "#5CD3F0"
  temp-28: "#D8E4EC"
  temp-36: "#FFB547"
  temp-43: "#FF8F4A"
  # Dawn theme (light)
  dawn-canvas: "#F5F3ED"
  dawn-surface: "#FFFFFF"
  dawn-surface-raised: "#ECEFF5"
  dawn-border-strong: "#6B778E"
  dawn-ink: "#0B1222"
  dawn-ink-muted: "#4A5670"
  dawn-cold: "#0A6E8C"
  dawn-warm: "#9C5200"
  dawn-link: "#0B5FA5"
  dawn-success: "#1C7A4A"
  dawn-warning: "#8A5B00"
  dawn-danger: "#B42318"
typography:
  display:
    fontFamily: Bricolage Grotesque
    fontSize: 4.5rem
    fontWeight: 700
    lineHeight: 1.0
    letterSpacing: -0.03em
  headline-lg:
    fontFamily: Bricolage Grotesque
    fontSize: 2.75rem
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Bricolage Grotesque
    fontSize: 1.75rem
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Bricolage Grotesque
    fontSize: 1.25rem
    fontWeight: 600
    lineHeight: 1.3
  body-lg:
    fontFamily: Inter
    fontSize: 1.1875rem
    fontWeight: 400
    lineHeight: 1.6
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  label-md:
    fontFamily: Inter
    fontSize: 0.9375rem
    fontWeight: 600
    lineHeight: 1.2
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 0.75rem
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0.08em
  readout-lg:
    fontFamily: JetBrains Mono
    fontSize: 3rem
    fontWeight: 600
    lineHeight: 1.0
    letterSpacing: -0.02em
    fontFeature: '"tnum" 1, "zero" 1'
  readout-md:
    fontFamily: JetBrains Mono
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: '"tnum" 1, "zero" 1'
  code:
    fontFamily: JetBrains Mono
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.6
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 14px
  full: 9999px
spacing:
  2xs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 40px
  2xl: 64px
  3xl: 104px
  gutter: 16px
  max-width: 1200px
components:
  page:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
  page-dawn:
    backgroundColor: "{colors.dawn-canvas}"
    textColor: "{colors.dawn-ink}"
    typography: "{typography.body-md}"
  hero-headline:
    textColor: "{colors.ink}"
    typography: "{typography.display}"
  hero-readout:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.cold}"
    typography: "{typography.readout-lg}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.canvas}"
    typography: "{typography.label-md}"
    rounded: "{rounded.full}"
    padding: 14px
    height: 48px
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.canvas}"
  button-primary-dawn:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.dawn-ink}"
    rounded: "{rounded.full}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.label-md}"
    rounded: "{rounded.full}"
    padding: 14px
    height: 48px
  button-secondary-dawn:
    backgroundColor: "{colors.dawn-surface}"
    textColor: "{colors.dawn-ink}"
    rounded: "{rounded.full}"
  link:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.cold}"
  link-dawn:
    backgroundColor: "{colors.dawn-canvas}"
    textColor: "{colors.dawn-link}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  card-dawn:
    backgroundColor: "{colors.dawn-surface}"
    textColor: "{colors.dawn-ink}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  card-meta:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body-sm}"
  card-meta-dawn:
    backgroundColor: "{colors.dawn-surface}"
    textColor: "{colors.dawn-ink-muted}"
    typography: "{typography.body-sm}"
  kit-card:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  kit-card-dawn:
    backgroundColor: "{colors.dawn-surface-raised}"
    textColor: "{colors.dawn-ink}"
    rounded: "{rounded.lg}"
  kit-readout-cold:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.temp-20}"
    typography: "{typography.readout-md}"
  kit-readout-coldest:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.temp-13}"
    typography: "{typography.readout-md}"
  kit-readout-cold-dawn:
    backgroundColor: "{colors.dawn-surface-raised}"
    textColor: "{colors.dawn-cold}"
    typography: "{typography.readout-md}"
  kit-readout-warm:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.temp-43}"
    typography: "{typography.readout-md}"
  kit-readout-warm-dawn:
    backgroundColor: "{colors.dawn-surface-raised}"
    textColor: "{colors.dawn-warm}"
    typography: "{typography.readout-md}"
  curve-neutral-label:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.temp-28}"
    typography: "{typography.readout-md}"
  curve-warm-label:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.temp-36}"
    typography: "{typography.readout-md}"
  status-done:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.success}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.full}"
  status-done-dawn:
    backgroundColor: "{colors.dawn-surface}"
    textColor: "{colors.dawn-success}"
    typography: "{typography.label-caps}"
  status-help-wanted:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.full}"
  status-help-wanted-dawn:
    backgroundColor: "{colors.dawn-surface}"
    textColor: "{colors.dawn-warm}"
    typography: "{typography.label-caps}"
  safety-callout:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.warning}"
    typography: "{typography.label-md}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  safety-callout-dawn:
    backgroundColor: "{colors.dawn-surface}"
    textColor: "{colors.dawn-warning}"
    rounded: "{rounded.md}"
  error-text:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.danger}"
  error-text-dawn:
    backgroundColor: "{colors.dawn-surface}"
    textColor: "{colors.dawn-danger}"
  hairline-rule:
    backgroundColor: "{colors.hairline}"
    height: 1px
  input-border:
    backgroundColor: "{colors.border-strong}"
    width: 1px
  input-border-dawn:
    backgroundColor: "{colors.dawn-border-strong}"
    width: 1px
  focus-ring:
    backgroundColor: "{colors.cold}"
    width: 2px
  focus-ring-dawn:
    backgroundColor: "{colors.dawn-link}"
    width: 2px
  code-block:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink}"
    typography: "{typography.code}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  eyebrow:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label-caps}"
  section-title:
    textColor: "{colors.ink}"
    typography: "{typography.headline-lg}"
  card-title:
    textColor: "{colors.ink}"
    typography: "{typography.headline-md}"
  table-head:
    textColor: "{colors.ink-muted}"
    typography: "{typography.headline-sm}"
  lead:
    textColor: "{colors.ink}"
    typography: "{typography.body-lg}"
  layout-container:
    width: "{spacing.max-width}"
    padding: "{spacing.gutter}"
  section:
    padding: "{spacing.3xl}"
  stack:
    padding: "{spacing.2xl}"
  cluster-gap:
    padding: "{spacing.xl}"
  chip:
    rounded: "{rounded.sm}"
    padding: "{spacing.xs}"
  chip-tight:
    padding: "{spacing.2xs}"
  inline-gap:
    padding: "{spacing.sm}"
  diagram-frame:
    rounded: "{rounded.none}"
---

# Open Bed Climate — DESIGN.md

The visual contract for the Open Bed Climate website (Astro, static, English). Full rationale, wireframes and component
specs: [`website/plan/04-design.md`](website/plan/04-design.md). This file is authoritative for tokens; change it
first, then mirror into CSS custom properties (`npx @google/design.md export --format css-vars DESIGN.md`).

## Overview

**Thermal Night.** A calm, dark night-sky canvas where the only color is *temperature*. Cold cyan and warm amber
are not decoration: they are mapped to the real 13–43 °C setpoint range of the system, so every accent on the page
means something. Illustrations are hairline engineering schematics (the water loop, the hub, an exploded kit), never
renders or photos. That honesty fits the project's state (design phase, no measured build yet) and speaks to makers;
the calm, dark, low-contrast-chroma canvas keeps it sleep-related and gives sponsors a polished, serious surface.

Tone references are abstract, not brand imitations: an instrument panel at night, a thermal camera's palette
reduced to two hues, a datasheet drawing.

## Colors

- **Night (default) canvas `#070B16`, surface `#0E1528`, surface-raised `#16203B`:** three steps of depth, no
  shadows needed. `hairline #2A3A63` for decorative rules and diagram strokes only (not a control boundary).
- **`border-strong #56688F`:** every interactive boundary (inputs, secondary buttons) — ≥ 3:1 against the surfaces.
- **Ink `#E9EEF7`, ink-muted `#A3B0C8`:** text. Muted is ≥ 7:1, safe for body copy.
- **Primary (warm amber) `#FFB547`:** the action color. Primary CTAs (build, contribute, sponsor). Warmth = human invitation.
- **Cold `#5CD3F0`:** links, focus rings, live readouts. Cold = information.
- **Temperature scale `temp-13 … temp-43`:** used for curves, gradients, kit readouts. A gradient is always
  `temp-13 → temp-20 → temp-28 → temp-36 → temp-43` in that order and always labelled with °C values.
- **Dawn (light) theme:** paper canvas `#F5F3ED`, white surfaces. On light backgrounds the mid-tone cyan/amber fail
  contrast, so text and graphic strokes switch to `dawn-cold #0A6E8C` and `dawn-warm #9C5200`. The primary button
  keeps its amber fill with dark ink text (10.6:1).
- **Status:** success / warning / danger per theme. Warning is reserved for the safety callout.

## Typography

- **Display and headlines: Bricolage Grotesque** (OFL, variable, self-hosted via Fontsource) 600/700. Slightly
  quirky, humane grotesque: maker energy without looking like a toy.
- **Body and UI: Inter** (OFL) 400/600. `body-md` 16px, `body-lg` 19px for intros.
- **Readouts, labels, code: JetBrains Mono** (OFL) 400/600 with tabular, slashed-zero figures. Every temperature,
  wattage and part number is set in mono so numbers line up and feel measured.
- `label-caps` is mono, uppercase via CSS, 0.08em tracking. Only for eyebrows and status chips.
- Max three families, max two weights per family on a page. Measure 60–72ch for prose.

## Layout

- 4px base grid; spacing scale 4/8/12/16/24/40/64/104 px.
- Container max 1200px, 16px side gutter on phones, 24px ≥ 640px, 40px ≥ 1024px. No horizontal page scroll.
- Breakpoints: `sm 640px`, `md 900px`, `lg 1200px`. Grids: 1 column → 2 (sm) → 3 (md) for pillar/kit/sponsor cards.
- Sections are separated by space (`3xl`) and a full-width hairline, not by alternating background colors.

## Elevation & Depth

Depth comes from the three surface steps, not shadows. The only glow allowed is the temperature gradient behind the
hero bed outline (blurred, ≤ 24% opacity). Cards lift on hover by switching `surface → surface-raised` and a 1px
`border-strong` outline; no transform jumps.

## Shapes

- Cards `lg` 14px, code blocks and callouts `md` 8px, chips `sm` 4px, buttons `full` (pill).
- Diagrams use square corners (`none`) and 1.5px strokes: they are drawings, not UI.

## Components

- **button-primary:** warm fill, canvas-colored text, pill, 48px tall. One per viewport region.
- **button-secondary:** surface fill, ink text, 1px `border-strong`, pill.
- **link:** cold, underlined on hover and always underlined inside prose.
- **card / kit-card:** surface (or raised) fill, `lg` radius, `lg` padding. Kit cards carry a mono temperature
  readout (coldest water, warm cap 43 °C) colored from the temperature scale *plus* the printed value.
- **status chip:** `status-done` (success) or `status-help-wanted` (warm). Never a "shipping" or "available" state
  while the project is in design phase.
- **safety-callout:** surface with a warning-colored left rule and icon, links to `SAFETY.md`. Required on home
  and every kit page.
- **focus-ring:** 2px solid cold (dawn: link blue), 2px offset, never removed.
- **hero-readout:** the large mono °C number in the hero, tied to the animated night curve.

## Do's and Don'ts

- Do use color only for temperature meaning or a single primary action.
- Do print the °C value next to any color that encodes temperature (color is never the only carrier).
- Do draw illustrations as hairline schematics in `ink-muted`/`hairline`, with temperature color only on water paths.
- Don't use product photos, renders or stock bedroom imagery.
- Don't use any other company's logos, product names in visuals, colors or styling; the non-affiliation note lives
  in the footer.
- Don't animate anything that cannot be paused or that ignores `prefers-reduced-motion`.
- Don't use warning yellow for anything but safety content.
