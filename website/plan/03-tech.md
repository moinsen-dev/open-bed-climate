# 03 — Technical architecture

Read: README.md · hardware/kits/*.toml · hardware/parts.toml · docs/FEATURES.md ·
software/opod/src/opod/{thermal,schedule,kit,golden,render_parts}.py · hub/esphome/opod-hub.yaml ·
hub/esphome/components/opod/test/schedule.txt · .github/workflows/test.yml · STATE.md · website/plan/01-content.md.
Versions were checked against the npm registry on 2026-10-11.

**Principle:** the repo is the source of truth and the site is a static view of it.
- Every number shown on the site comes from a repo file at build time.
- Every computed number comes from the Python reference implementation (`opod`), never from a second copy in TS.
- The single exception is the schedule curve. It is ported to TS and tested against the golden vectors the C++ hub
  port already uses (§3.2).

---

## 1. Stack

| Piece | Choice | Pin (exact, `--save-exact`) | Why |
|---|---|---|---|
| Framework | Astro 7, static output | `astro@7.3.5` | Current major (7.0.0 shipped 2026-06-22; latest 7.3.8 is from 2026-10-08). 7.3.5 has had more than 2 weeks of soak, so bump deliberately. It has a content layer with built-in TOML/YAML/MD loaders and Zod 4 via `astro/zod`. |
| Sitemap | `@astrojs/sitemap` | `3.7.4` | Needs `site`, see §5. |
| Feed | `@astrojs/rss` | `4.0.19` | Build-log RSS (02-community: "launch with this"). |
| Type check | `@astrojs/check` | `0.9.10` | Runs `astro check` in CI. |
| TypeScript | `typescript` | `6.0.3` | **Not 7.x.** `@astrojs/check@0.9.10` peers on `typescript ^5 \|\| ^6`. |
| TOML | `smol-toml` | `1.9.0` | Astro already bundles it. It is a **direct** dependency because the parts parser (§2.2) and the data test import it. |
| Link check | `linkinator` | `8.1.0` | Do **not** use the npm `lychee` package: it is an unrelated package abandoned in 2022. |
| Font | `@fontsource-variable/<family>` | `5.3.0` | Self-hosted woff2 bundled into `dist/`, so there are no requests to Google. The design plan picks the family. Load the Latin subset only and use `font-display: swap`. Mono uses the system `ui-monospace` stack. |
| Tests | `node:test` (built in) | Node 24 LTS | Zero dependencies. Node ≥ 22.18 / 24 strips TS types natively, so the tests import the same `src/lib/*.ts` the site uses. |

**Not used, on purpose:**
- **MDX.** All prose is plain `.md` from the repo. (If it is ever needed, use `@astrojs/mdx@8.0.3`, which needs `astro ^7.2.10`.)
- **No client framework.** No React, Preact or Svelte.
- **No Tailwind, no Vitest, no Lighthouse CI as a hard gate.**

**Styling: plain CSS with design tokens, no Tailwind.**
- There is one small site and two SVG islands.
- The charts read the same custom properties as the pages, e.g. `stroke: var(--c-cool)`. That gives light/dark mode
  for free with no build step.
- Astro scopes component `<style>` automatically, so the dependency count stays at zero.
- Files:
  - `src/styles/tokens.css`: colours, type scale, spacing, radii, with `prefers-color-scheme` overrides.
  - `src/styles/global.css`: reset, base elements, `.prose` for rendered docs.

**Islands: two only, both vanilla TS in an Astro `<script>`, which Astro bundles and loads as a module.**
- Both are server-rendered first and work without JS:
  1. the kit picker
  2. the schedule editor
- The thermal estimator is **not** an island. It is precomputed and rendered as a static table (§3.3).

---

## 2. Single source of truth: build-time data

All collections are defined in `src/content.config.ts`.
- Paths are relative to `website/`, so `..` is the repo root.
- Schemas live in `src/lib/schemas.ts` so that `test/data.test.ts` validates the raw repo files with the **same**
  Zod objects.

```ts
// src/lib/schemas.ts
import { z } from "astro/zod"; // Zod 4, re-exported by Astro; no separate zod dependency

export const SENSING = ["none", "load_cells", "pneumatic", "piezo_grid"] as const; // = opod.kit.SENSING_OPTIONS
export const PART_STATUS = ["datasheet", "listing", "unverified", "rejected"] as const; // = render_parts.BADGE keys

// Mirrors opod.kit.load_kit. Top level is strict: same rule as ALLOWED_TOP.
// Inner tables are not strict, because Python only rejects unknown *sections*. FORBIDDEN_KEYS stay Python's job (CI).
export const kitSchema = z.strictObject({
  kit: z.object({
    name: z.string(),
    tier: z.union([z.literal(0), z.literal(1)]),
    zones: z.union([z.literal(1), z.literal(2)]),
  }),
  thermal: z.object({
    tec_per_zone: z.int().min(1).max(6),
    heatsink_k_per_w: z.number().positive(),
    max_tec_current_a: z.number().min(1).max(6), // MAX_TEC_CURRENT_A
  }),
  sensing: z.object({ option: z.enum(SENSING) }),
  power: z.object({ tec_psu_w_per_zone: z.number().positive(), aux_psu_w: z.number().positive() }),
  claims: z.object({ min_water_c: z.number(), max_water_c: z.number().max(43) }),
});

export const partRoleSchema = z.object({
  id: z.string(),
  module: z.string(), // Power | Control | Hub | Thermal | Water mat | Sensing | Add-ons. Ordered in src/site.ts; unknown ones go last.
  safety: z.boolean(),
  requirement: z.string(),
  notes: z.string().optional(),
  example: z.array(z.object({
    name: z.string(),
    status: z.enum(PART_STATUS),
    source: z.url(),
    verified_on: z.iso.date(), // quoted "2026-10-10" in TOML → string
    notes: z.string().optional(),
  })).default([]),
});

export const FEATURE_STATE = { "✅": "now", "🔜": "planned", "🔌": "third_party", "❌": "out_of_scope" } as const;
export const featureSchema = z.object({
  row: z.int(),          // 0-based order in the FEATURES.md table (feature-names.yaml is keyed by it)
  pod: z.string(),       // column 1. Kept for the CI row-count check, never rendered (01-content §3)
  approach: z.string(),  // markdown, rendered inline
  module: z.string(),
  status: z.array(z.object({ state: z.enum(["now", "planned", "third_party", "out_of_scope"]), note: z.string() })),
});
```

```ts
// src/content.config.ts
import { defineCollection } from "astro:content";
import { glob, file } from "astro/loaders";
import { parse } from "smol-toml";
import { kitSchema, partRoleSchema, featureSchema } from "./lib/schemas.ts";
import { featuresLoader } from "./lib/features.ts";
import { z } from "astro/zod";

// 2.1 Kits: one TOML file per entry. id = filename slug (solo-starter, duo-standard, duo-reference)
const kits = defineCollection({
  loader: glob({ pattern: "*.toml", base: "../hardware/kits" }),
  schema: kitSchema,
});

// 2.2 Parts: the top level is { role: [...] }, so file()'s default parser would produce a single entry "role". Unwrap it.
const parts = defineCollection({
  loader: file("../hardware/parts.toml", { parser: (text) => (parse(text) as { role: unknown[] }).role }),
  schema: partRoleSchema, // each role has a unique `id`, which file() requires
});

// 2.3 Feature table, parsed out of docs/FEATURES.md (inline object loader, see below)
const features = defineCollection({ loader: featuresLoader("../docs/FEATURES.md"), schema: featureSchema });

// 2.4 Repo docs rendered in place (§2.5). id = route slug
const DOC_FILES = ["SAFETY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "docs/design/*.md", "hardware/WIRING.md"];
const docs = defineCollection({
  loader: glob({
    pattern: DOC_FILES,
    base: "..",
    generateId: ({ entry }) => entry.replace(/^docs\//, "").replace(/\.md$/, "").toLowerCase(), // safety, design/00-architecture, hardware/wiring
  }),
  // repo docs have no frontmatter; the title comes from the first heading in render()
});

// 2.6 Hand-maintained site data (owned by 01-content), each entry with a `source` pointer
const roadmap      = defineCollection({ loader: file("src/data/roadmap.yaml"),       schema: z.object({ id: z.string(), area: z.string(), state: z.enum(["done", "next", "measure"]), text: z.string(), source: z.string() }) });
const helpWanted   = defineCollection({ loader: file("src/data/help-wanted.yaml"),   schema: z.object({ id: z.string(), role: z.string(), task: z.string(), source: z.string(), link: z.string(), difficulty: z.enum(["easy", "medium", "hard"]) }) });
const sponsorAsks  = defineCollection({ loader: file("src/data/sponsor-asks.yaml"),  schema: z.object({ id: z.string(), ask: z.string(), unlocks: z.string(), source: z.string() }) });
const featureNames = defineCollection({ loader: file("src/data/feature-names.yaml"), schema: z.object({ id: z.string(), row: z.int(), name: z.string() }) });
const issueTemplates = defineCollection({ loader: glob({ pattern: ["*.yml", "!config.yml"], base: "../.github/ISSUE_TEMPLATE" }), schema: z.object({ name: z.string(), description: z.string().optional() }) });

// 2.7 Hand-written longform copy blocks (01-content: "copy lives in website/src/content/")
const copy = defineCollection({ loader: glob({ pattern: "**/*.md", base: "src/content/copy" }) });

export const collections = { kits, parts, features, docs, roadmap, helpWanted, sponsorAsks, featureNames, issueTemplates, copy,
  log, contributors, sponsors }; // last three: §7
```

**FEATURES.md → structured data** (`src/lib/features.ts`). The parser is a pure function so `node --test` can run it.

```ts
export function parseFeatureTable(md: string): FeatureRow[] {
  // Take the first table whose header starts with "| Pod 6 feature". Skip the |---| line, read rows until the first non-"|" line.
  // Split cells on unescaped "|", trim. Status cell "✅ basic, 🔜 adaptive" → split on ",",
  // map the leading emoji via FEATURE_STATE, keep the rest as note ("basic", "(on purpose)").
  // Throw on an unknown emoji or a column count ≠ 4, so a malformed edit breaks the build loudly.
}
export const featuresLoader = (path: string): Loader => ({
  name: "features-md",
  load: async ({ store, parseData, renderMarkdown, watcher }) => {
    // read file → parseFeatureTable → for each row: data = await parseData({ id: String(row.row), data: row });
    // store.set({ id, data, rendered: await renderMarkdown(row.approach) }); watcher?.add(absPath) for dev reload
  },
});
```

`renderMarkdown` has been on the loader context since Astro 5.9. If the pinned version changes this API, render the
inline Markdown in the page instead with the same remark pipeline.

**2.5 Rendering repo docs.**
- **Rendered in place:**
  - `SAFETY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`
  - `docs/design/*.md`
  - `hardware/WIRING.md`
  
  Rationale: SAFETY tables must never be retyped (01-content), and the design docs are what contributors read.
- **Everything else** links to `${REPO_URL}/blob/main/<path>`. That covers:
  - code, TOML
  - `docs/research/*`
  - `PARTS.md`, which is generated anyway; the site renders `parts.toml` directly.
- **Relative links inside those docs break when rendered** (`research/prior-art.md`, `../SAFETY.md`). The fix is a
  ~30-line remark plugin with no dependencies, `src/lib/remark-repo-links.ts`. It walks the mdast `link` and `image`
  nodes and resolves each relative URL against the source file's repo path (`file.path` relative to the repo root):
  - target is in the docs collection → `/docs/<id>/` + hash
  - target is the kit/parts TOML → `/kits/<id>/` or `/parts/`
  - otherwise → `${REPO_URL}/blob/main/<path>` (or `/tree/main/` for directories)
  
  Register it in `astro.config.mjs → markdown.remarkPlugins`.
- `/safety/` is a real 301 to `/docs/safety/` via `public/_redirects` (`/safety/ /docs/safety/ 301`), which CF Pages
  serves at the edge. Don't use Astro `redirects`, which emits a meta-refresh page.

**2.8 Constants** live in `src/site.ts`:
- `REPO_URL`: placeholder until the owner decides (01-content §7.1). It is the only place it appears.
- `SITE_NAME`
- `NAV`, `FOOTER_NAV`
- `MODULE_ORDER`
- `STATUS_LABEL` (words, never emoji; 01-content §6)

---

## 3. Computed data and interactive pieces

### 3.1 Precomputed model data: Python writes JSON, the site reads it

The model is never ported to TS. This mirrors the repo's existing pattern (`python -m opod.golden` →
`schedule.txt`, `render_parts` → `PARTS.md`, each with a pytest freshness test).

- **New module `software/opod/src/opod/site_data.py`**, usage: `cd software/opod && uv run python -m opod.site_data`.
  - It writes `website/src/data/model.json`, which is **committed**.
  - The CF Pages build then needs **no Python or uv**.
- **Small refactor in `opod/kit.py`:** extract `coldest_water(kit, t_ambient) -> (t_water_c, tec_power_w)` from the
  current-sweep loop in `check_kit`. `check_kit` then calls it with 25.0, so there is one implementation of the sweep.
- **New pytest `test_site_data_up_to_date`** in `tests/test_kits.py`. It works like `test_golden_vectors_up_to_date`:
  `assert DST.read_text() == build()`, with the message "run: python -m opod.site_data".
- **Cost:** ≈ 0.55 s per kit per ambient, so 3 kits × 4 ambients ≈ 6–7 s added to the `reference` job. Keep the grid
  at 4 ambients.
- **Output** is stable JSON: `sort_keys=True`, indent 2, values rounded to 0.1 °C / 1 W so float noise never makes
  it stale.

```json
{
  "generated_by": "python -m opod.site_data (do not edit)",
  "limits": { "setpoint_min_c": 13.0, "setpoint_max_c": 43.0 },
  "schedule_default": { "points": [[0, 24.0], [30, 21.0], [120, 20.0], [300, 23.0], [420, 25.0]],
                        "wake_ramp_min": 30.0, "wake_target_c": 32.0 },
  "kits": {
    "solo-starter": {
      "name": "Solo Starter",
      "check": { "min_water_c": 21.5, "max_water_c": 43.0, "tec_input_w_per_zone": 173, "aux_w": 40,
                 "zone_current_limit_a": 15.0, "problems": [] },
      "coldest_by_room": [ { "room_c": 20, "water_c": "<model>", "tec_input_w": "<model>" },
                           "... rooms 25, 28, 30 (same shape)" ]
    }
  }
}
```

- **`max_water_c` is `min(raw, 43.0)`.** Raw `check_kit` returns 57–67 °C for an empty bed, which is meaningless
  past the safety cap.
- Keys are the kit filename stems, i.e. the same ids as the `kits` collection.
- `limits` and `schedule_default` come straight from `opod.control` and `opod.schedule.DEFAULT`, so TS never
  restates them.

**Which number is the headline (resolves the README/claims/model mismatch, 01-content C1):**
- **Headline:** the TOML claim (21.7 / 18.8 / 18.5 °C). It is the kit's promise, and CI already proves it holds.
- **Secondary detail:** the model value (21.5 / 18.6 / 18.3 °C), shown as "model estimate".
- Every temperature renders through `<ModelEstimate>`, which adds the "model estimate, no prototype measured yet"
  footnote.

### 3.2 Schedule visualizer (`/schedule/`): TS port tested against shared golden vectors

`src/lib/schedule.ts` is a port of `opod/schedule.py`, about 40 lines:
- `base(points, minute)`: linear interpolation between sorted `(minute, °C)` points, held flat before the first
  point and after the last.
- `setpoint(s, minute, wakeMinute | null) → number | null`:
  - returns `null` at or after the wake time (the side turns off)
  - inside `(wake − wake_ramp_min, wake)` it ramps linearly from `base(rampStart)` to `wake_target_c`
- `wakeOffset(startMinOfDay, wakeMinOfDay)` = `((wake − start) mod 1440) || 1440`.
- `validate(points)`: rejects empty or unsorted points and setpoints outside `limits` from `model.json`.

**Contract:** `test/schedule.test.ts` parses `hub/esphome/components/opod/test/schedule.txt`, the file generated by
`python -m opod.golden` that the C++ port is already tested against.
- The file has **two** P/R blocks: the default curve at lines 4–5 and a second curve `P 0 22 60 16 240 18.5` / `R 20 35`
  at lines 369–370. Each `S` line is checked against the P/R block before it.
- `P` line: points. `R` line: ramp minutes and wake target.
- `S <minute> <wake|-> <expected|off>`: `off` means `null`.
- `W <start> <wake> <offset>`.
- Every `S` line must match within 1e-4; every `W` line must match exactly.

That makes three ports (Python, C++ and TS) against one spec. The test also asserts that the **first** `P`/`R` block equals
`model.json.schedule_default`.

**UI (`ScheduleEditor.astro` plus a `<script>` of about 150 lines):**
- Server-rendered: an SVG of the default curve (x = time from bedtime, y = °C), drawn by the same `schedule.ts` at
  build time. Without JS, the page is a static chart.
- With JS:
  - drag points (pointer events, keyboard arrows on focused handles)
  - add a point (double-click) or remove one (Delete)
  - bedtime and wake inputs (`<input type="time">`)
  - wake ramp and wake target fields
  - clamping to `limits`
  - the off segment after wake is shown dashed
- **CSP-safe drawing:** handles and the curve move only through SVG attributes (`cx`, `cy`, `d`, `transform`) and class
  toggles, never `element.style` or `style="…"`. `style-src 'self'` blocks inline style attributes as well.
- **Output:** a "Copy for your hub" button generates the exact `points:` / `wake_ramp:` / `wake_temperature:` YAML
  block from `hub/esphome/opod-hub.yaml`, for example `- { at: 30min, temperature: 21 }`. No storage, no network.
- **Accessibility:** a `<table>` of the points mirrors the chart and is editable. The SVG has `role="img"` and a
  generated `aria-label` summary.

### 3.3 Kit comparison, picker and "what can my kit do"

**Comparison** (`/kits/`, static): one table with kits as columns, built from the `kits` collection joined with
`model.json.kits[id]`:
- zones, tier, TECs per zone, current cap, zone current limit, sensing option
- PSUs: TEC W per zone and aux W
- claimed coldest / warmest water, with the model value as detail
- TEC input power, and whether the PSU margin is within 80 %

**"What can my kit do" estimator: static, no island.**
- Under the comparison: a "coldest water by room temperature" table (rooms 20 / 25 / 28 / 30 °C × kits) from
  `coldest_by_room`, plus the TEC input power at that point.
- The same table filtered to one kit appears on `/kits/[id]/`.
- No sliders, because the model only has meaning at the precomputed points and anything else would invent numbers.
- Custom builds get the "copy a TOML and run `uv run pytest`" CTA. That is the real estimator, and it keeps one
  implementation.

**Picker** (`KitPicker.astro` plus a `<script>` of about 60 lines, progressive enhancement over the table):
- It asks three radio questions:
  1. how many sleepers → `zones`
  2. whether a qualified person can assemble a mains power module and custom PCBs → allows `tier 1`
  3. biometrics priority → prefers `sensing` (`load_cells` < `pneumatic` < `piezo_grid`)
- It then highlights the matching column and scrolls to it.
- The rules read `data-*` attributes rendered from the kit data, so a new kit TOML is picked up with no JS change.
- Without JS the questions are hidden (`hidden` attribute removed by the script) and the table is the page.

---

## 4. Build, test, CI

**`website/package.json` scripts:**

```json
{
  "type": "module",
  "engines": { "node": ">=22.18" },
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "check": "astro check",
    "test": "node --test \"test/*.test.ts\"",
    "budget": "node scripts/budget.mjs",
    "links": "linkinator dist --recurse --skip \"^https?://(?!localhost)\"",
    "data": "cd ../software/opod && uv run python -m opod.site_data",
    "guard": "node scripts/guard.mjs",
    "verify": "npm run check && npm test && npm run build && npm run budget && npm run guard && npm run links"
  }
}
```

**`tsconfig.json`:**
- extends `astro/tsconfigs/strict`
- `"allowImportingTsExtensions": true`, `"erasableSyntaxOnly": true` and `"verbatimModuleSyntax": true`
- These settings let `src/lib/*.ts` run unchanged under Node's type stripping. Three rules apply to **every** file in
  `src/lib/`, and `astro check` enforces them:
  1. Relative imports carry the `.ts` extension (`./schemas.ts`).
  2. Type-only imports use `import type { … }`.
  3. JSON is imported as `import model from "../data/model.json" with { type: "json" }`.
- No enums, namespaces or parameter properties. Lib files must not import `astro:*` virtual modules. Only
  `content.config.ts` and pages do; `astro/zod` is a real package export and is fine.

**`.nvmrc`:** `24`.

**Tests (`website/test/`, `node:test`):**
- `schedule.test.ts`: the golden-vector contract in §3.2.
- `features.test.ts`:
  - `parseFeatureTable(FEATURES.md)` returns ≥ 15 rows and every status maps to a known state
  - a malformed fixture throws
- `data.test.ts`: the "site data matches repo" test.
  - Every `hardware/kits/*.toml` parses with `smol-toml` and passes `kitSchema`.
  - The set of kit ids equals the keys of `model.json.kits`, and the names match.
  - For each kit: `claims.min_water_c >= model.check.min_water_c - 0.1` (the same tolerance as `check_kit`) and
    `model.check.problems` is empty.
  - `parts.toml` passes `partRoleSchema`, and role ids are unique.
  - The `feature-names.yaml` row count equals the FEATURES.md row count (01-content §6).

**Content guard (post-build) — `scripts/guard.mjs`.** It runs after `build` in `verify`, so it can never be skipped
because `dist/` is missing. It scans `dist/**/*.html` and fails when:
- "Pod-class" or "Eight Sleep" appear outside the allowed pages (`/about/`, `/features/`, count per 01-content §6)
- any emoji appears inside a `.status` element
- any inline `<script>` without `src`, or any `style="` attribute, appears (CSP check, §5)
- **any third-party request on page load** (02-community §4.1). That means an absolute URL whose origin is not the
  site's own on a resource-loading element or attribute:
  - `script[src]`, `link[href]` except `rel=canonical|alternate`, `img[src|srcset]`, `source`, `video[poster]`
  - `iframe`, `object`, `embed`
  - CSS `url()` and `@import` in `dist/**/*.css`
  
  Plain `<a href>` links are allowed. At runtime the CSP in §5 (`default-src 'self'`) enforces the same rule in the
  browser, so this is a static check backed by a runtime one.

**Byte budget (hard gate) — `scripts/budget.mjs`.** It walks `dist/`. Per page, it sums the referenced JS and CSS
(gzip, via `node:zlib`) and fails when either of these is exceeded:

| Budget | Limit |
|---|---|
| JS per page | ≤ 15 KB gz on `/schedule/` and `/kits/`, ≤ 1 KB on pages with a click-to-load video, 0 KB on every other page |
| CSS total | ≤ 20 KB gz |
| HTML per page | ≤ 60 KB gz |
| Fonts per page | ≤ 2 files |

Rationale: this is deterministic, unlike Lighthouse.

**Lighthouse: advisory only, run locally or on a preview.**
- Target ≥ 95 for Performance, Accessibility, Best Practices and SEO.
- Check it with the chrome-devtools `lighthouse_audit` tool against `astro preview`.
- It is not a CI gate: it is flaky on shared runners, and `@lhci/cli` hasn't been released since 2025.

**Link check:**
- Internal links only for now, because no remote exists, so every `REPO_URL` link would 404.
- Once the repo is public, add a weekly scheduled `lycheeverse/lychee-action` job for external links.

**CI: add this job to `.github/workflows/test.yml`.** Model freshness is already enforced in `reference` by the new
pytest.

```yaml
  website:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: website
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: website/.nvmrc
          cache: npm
          cache-dependency-path: website/package-lock.json
      - run: npm ci
      - run: npm run verify
```

---

## 5. Deployment: Cloudflare Pages, static

**`astro.config.mjs`:**

```js
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import remarkRepoLinks from "./src/lib/remark-repo-links.ts";

export default defineConfig({
  site: process.env.SITE_URL ?? "https://open-pod.pages.dev", // custom domain TBD (01-content §7.4)
  output: "static",
  trailingSlash: "always",
  build: { format: "directory", inlineStylesheets: "never" },
  markdown: { remarkPlugins: [remarkRepoLinks] },
  integrations: [sitemap()],
});
```

**Cloudflare Pages project `open-pod`:**
- Once the repo has a remote, use the Git integration:
  - root directory `website`
  - build command `npm ci && npm run build`
  - output `dist`
  - env `NODE_VERSION=24` and `SITE_URL=<domain>`
  
  Preview deploys per branch come for free.
- Until then, deploy manually: `npx wrangler pages deploy dist --project-name=open-pod`, following the existing
  moinsen CF Pages recipe. For a `*.moinsen.dev` preview, the custom domain attach and CNAME follow that recipe.

**Privacy and security, enforced rather than promised:**
- No server, no Functions, no cookies, no analytics, no third-party requests. Fonts are self-hosted, and there are
  no external images or embeds.
- `public/_headers`:

```
/*
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; connect-src 'none'; frame-src https://www.youtube-nocookie.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self' <NEWSLETTER_ORIGIN>
  Referrer-Policy: no-referrer
  X-Content-Type-Options: nosniff
  Permissions-Policy: interest-cohort=(), camera=(), microphone=(), geolocation=()
/_astro/*
  Cache-Control: public, max-age=31536000, immutable
```

- `inlineStylesheets: "never"` keeps `style-src 'self'` valid.
- Astro may inline small processed `<script>`s. If the build emits inline scripts:
  - prefer Astro's built-in CSP option (`security.csp`, hash-based) if it is stable in the pinned version
  - otherwise move the two island scripts to `src/scripts/*.ts` imported via `<script src>`
  - `scripts/guard.mjs` fails the build on any inline script
- Images: `astro:assets` (sharp, bundled with Astro) for any future prototype photos. Diagrams are inline SVG
  components.
- `public/robots.txt` allows everything and points to `/sitemap-index.xml`.

---

## 6. Directory layout: every file to create

```
website/
├── .nvmrc                          # 24
├── .gitignore                      # node_modules, dist, .astro
├── README.md                       # dev commands, data flow (repo files → collections; opod.site_data → model.json)
├── package.json / package-lock.json
├── astro.config.mjs
├── tsconfig.json
├── plan/                           # 01-content.md, 02-*.md, 03-tech.md (this file)
├── public/
│   ├── _headers
│   ├── _redirects                  # /safety/ → /docs/safety/ 301
│   ├── robots.txt
│   └── favicon.svg
├── scripts/
│   ├── budget.mjs                  # byte budget (§4)
│   └── guard.mjs                   # post-build content + CSP guard (§4)
├── test/
│   ├── schedule.test.ts            # golden vectors from hub/.../schedule.txt
│   ├── features.test.ts
│   ├── data.test.ts                # site data ↔ repo (§4)
│   └── fixtures/features-bad.md
└── src/
    ├── content.config.ts           # all collections (§2)
    ├── site.ts                     # REPO_URL, SITE_NAME, NAV, FOOTER_NAV, MODULE_ORDER, STATUS_LABEL
    ├── data/
    │   ├── model.json              # GENERATED by python -m opod.site_data. Do not edit.
    │   ├── roadmap.yaml            # 01-content
    │   ├── help-wanted.yaml        # 01-content §5
    │   ├── sponsor-asks.yaml       # 01-content
    │   ├── sponsors.yaml           # 02-community tiers; logos in src/assets/sponsors/
    │   └── feature-names.yaml      # 01-content, keyed by FEATURES.md row
    ├── content/copy/               # hand-written longform blocks (home hero, tier explainer, …) as .md
    ├── content/log/                # build-log posts (.md, frontmatter: title, date, summary)
    ├── assets/sponsors/            # sponsor logos, committed (never hotlinked)
    ├── lib/
    │   ├── schemas.ts              # Zod schemas shared by content.config and tests
    │   ├── features.ts             # parseFeatureTable + featuresLoader
    │   ├── schedule.ts             # port of opod/schedule.py
    │   ├── hub-yaml.ts             # schedule → hub YAML snippet
    │   ├── kits.ts                 # join kit entry + model.json, sorting, labels
    │   └── remark-repo-links.ts    # rewrite relative links in rendered repo docs
    ├── styles/
    │   ├── tokens.css
    │   └── global.css
    ├── layouts/
    │   ├── Base.astro              # head, meta/OG, font preload, header, footer
    │   └── Doc.astro               # .prose wrapper + "Edit on GitHub" link + table of contents from headings
    ├── components/
    │   ├── Header.astro · Footer.astro
    │   ├── PhaseBanner.astro       # "design phase, no prototype yet"
    │   ├── SafetyNote.astro · ModelEstimate.astro · Status.astro   # Status renders words, never emoji
    │   ├── KitCard.astro · KitTable.astro · KitRoomTable.astro     # KitRoomTable is the static estimator
    │   ├── KitPicker.astro         # island 1 (inline <script>)
    │   ├── PartRole.astro · PartStatus.astro
    │   ├── FeatureTable.astro
    │   ├── ScheduleChart.astro     # server-rendered SVG from lib/schedule.ts
    │   ├── ScheduleEditor.astro    # island 2 (wraps ScheduleChart, inline <script>)
    │   ├── SystemDiagram.astro     # inline SVG, drawn fresh. Never copy the README ASCII diagram (its "12 V" label is wrong)
    │   ├── Disclaimer.astro        # footer, build-page and biometrics variants (02-community §4.3)
    │   ├── VideoEmbed.astro        # click-to-load, island 3 (§7)
    │   └── NewsletterForm.astro    # plain HTML POST, no JS (§7)
    └── pages/
        ├── index.astro
        ├── how-it-works.astro      # includes #software (merges the proposed /software/ route; fewer routes)
        ├── kits/index.astro
        ├── kits/[id].astro         # getStaticPaths from the kits collection
        ├── parts.astro
        ├── features.astro
        ├── schedule.astro
        ├── status.astro
        ├── contribute.astro
        ├── sponsor.astro
        ├── about.astro
        ├── community.astro         # .all-contributorsrc + self-hosted avatars (§7)
        ├── log/index.astro         # build log list
        ├── log/[slug].astro
        ├── rss.xml.ts              # @astrojs/rss over the log collection
        ├── impressum.astro         # § 5 DDG (02-community §4.1). Copy is owner input
        ├── privacy.astro           # DSGVO page
        ├── docs/index.astro
        ├── docs/[...slug].astro    # getStaticPaths from the docs collection
        └── 404.astro
```

**Repo files touched outside `website/`:**
- `software/opod/src/opod/site_data.py` (new)
- `software/opod/src/opod/kit.py` (extract `coldest_water`; no behaviour change, and the existing tests prove it)
- `software/opod/tests/test_kits.py` (adds `test_site_data_up_to_date`)
- `.github/workflows/test.yml` (adds the `website` job)

**Build order for the implementer:**
1. `site_data.py` + refactor + pytest → verify: `uv run pytest -q` is green, and `model.json` exists.
2. Scaffold, schemas, collections → verify: `astro check` + `npm test` (data and schedule tests).
3. Pages and components → verify: `npm run build`.
4. Islands → verify: manual run in the browser plus a Lighthouse pass on `astro preview`.
5. Budget, links, CI job → verify: `npm run verify` is green locally.

---

## 7. Additions from 01-content and 02-community (2026-10-11)

**Routes.**
- Added `/how-it-works/` (with `#software`; there is no separate `/software/` route), `/status/`, `/sponsor/` and
  `/about/` from 01-content.
- Added `/community/`, `/log/` + `/rss.xml`, `/impressum/` and `/privacy/` from 02-community.
- `/builds/` comes later: it needs merged build TOMLs, which don't exist yet. When they do, it gets a `glob` collection
  over `hardware/builds/*.toml`, the same way as kits.
- Every new route is static and needs no JS.
- `/status/` reads `roadmap.yaml`. The five OPEN-DECISIONS measurements are entries with `state: "measure"`.

**Content rules enforced in code:**
- Temperatures come only from `kits[id].claims` (headline) and `model.json` (detail, labelled as a model estimate).
  README numbers are never read.
- `/features/` shows `feature-names.yaml[row].name` instead of column 1. A test checks the row count (§4).
- The `/features/` setpoint row reads "setpoint 13–43 °C; reachable range depends on the kit" (01-content C9). That
  sentence lives in `feature-names.yaml`, not in FEATURES.md.
- The project name may change (02-community §4.2), so `SITE_NAME` in `src/site.ts` is the only place it is written.
  Copy uses `{SITE_NAME}`, and the CF project name and domain stay neutral until the name is decided.

**Privacy hard rules (02-community §4.1) and how each is enforced:**

| Rule | Implementation | Enforced by |
|---|---|---|
| No cookies, no analytics, no storage | No Functions, no analytics script, no `localStorage` (the schedule editor keeps state in memory only) | CSP `connect-src 'none'`, guard (no third-party script) |
| Self-hosted fonts | `@fontsource-variable/*` bundled into `/_astro/` | CSP `font-src 'self'`, guard |
| GitHub avatars self-hosted | `contributors` collection, below | guard: no `avatars.githubusercontent.com` in `dist/` |
| No live embeds | `VideoEmbed.astro`, below | CSP allows frames only from `youtube-nocookie.com` and only after a click; guard: no `<iframe>` in built HTML |
| Zero third-party requests on load | — | `scripts/guard.mjs` (§4) in CI, plus CSP at runtime |
| Newsletter as a plain POST | `NewsletterForm.astro`: `<form method="post" action="{NEWSLETTER_URL}">` with email + listmonk list id, and the privacy link next to the button. Rendered only when `NEWSLETTER_URL` is set in `src/site.ts` | CSP `form-action 'self' <NEWSLETTER_ORIGIN>`. `<NEWSLETTER_ORIGIN>` is filled when listmonk exists; until then it is `'self'` only |

**`contributors` collection (self-hosted avatars):** an inline loader in `content.config.ts`.
1. It reads `../.all-contributorsrc` (JSON: `contributors[].{login, name, avatar_url, contributions[]}`).
2. If the file doesn't exist yet, it falls back to `GET https://api.github.com/repos/<owner>/<repo>/contributors`
   (uses `GITHUB_TOKEN` if set; unauthenticated 60/h is enough for builds).
3. The page renders each avatar with `<Image src={avatar_url + "&s=96"} width={48} height={48} />`, using
   `image.remotePatterns: [{ hostname: "avatars.githubusercontent.com" }]` in `astro.config.mjs`.
   - Astro downloads and optimises remote images **at build time** and emits them under `/_astro/`, so visitors
     never contact GitHub.
4. If GitHub is unreachable, the loader logs a warning and returns an empty list. The page then shows the
   "contributors: see GitHub" link, and the build still passes.

Server-side requests made at **build** time are fine. The rule is about **visitors**.

**`sponsors` collection:** `file("src/data/sponsors.yaml")` with `{id, name, tier, url, logo}`. `logo` is an
`image()` path into `src/assets/sponsors/`, so the files are committed and optimised. Nothing is hotlinked.

**`VideoEmbed.astro` (island 3, about 15 lines of JS):**
- It renders a self-hosted thumbnail (committed, `astro:assets`) plus a button: "Play video (loads YouTube, see
  privacy)".
- On click, the script inserts `<iframe src="https://www.youtube-nocookie.com/embed/<id>?autoplay=1">`, sized via
  attributes, never `style`.
- Without JS, the button is a plain link to the video.
- CSP: §5 already lists `frame-src https://www.youtube-nocookie.com`. The guard scans built HTML and CSS only, so
  the iframe URL inside the bundled click-handler JS doesn't trip it, while an `<iframe>` in HTML still fails it.
- `privacy.astro` has one line about this: "Videos load from YouTube (youtube-nocookie.com) only after you click play."
- Self-hosted MP4/WebM in `public/media/` with `<video controls preload="none">` is preferred when the file is
  small. It needs no CSP exception.

**`log` collection:** `glob({ pattern: "*.md", base: "src/content/log" })`, schema `{ title, date: z.coerce.date(),
summary }`. `src/pages/rss.xml.ts` uses `@astrojs/rss`. The feed is linked with
`<link rel="alternate" type="application/rss+xml">`, a same-origin URL, so the guard allows it.
