# Open Bed Climate website

Static Astro 7 site, English only. The repository is the CMS: every number on the site comes from a repo file
at build time, and every computed number comes from the Python reference implementation (`software/opod`).
Plans: `plan/01-content.md` (copy, honesty rules) · `plan/02-community-sponsors.md` (sponsor, legal) ·
`plan/03-tech.md` (architecture) · `plan/04-design.md` + `/DESIGN.md` ("Thermal Night" visuals).

## Commands

```sh
npm ci
npm run dev        # http://localhost:4321
npm run verify     # astro check → node tests → build → byte budget → content/CSP guard → internal link check
npm run preview    # serve dist/
npm run data       # regenerate src/data/model.json from the Python model (needs uv)
node scripts/gen-temp-css.mjs   # regenerate src/styles/temp-scale.css after changing src/lib/temp.ts
```

Node ≥ 22.18 (type stripping runs `src/lib/*.ts` directly in `node --test`). CI: the `website` job in
`.github/workflows/test.yml`. `model.json` freshness is checked by `test_site_data_up_to_date` in the `reference` job.

## Data flow

| Site data | Source | How |
|---|---|---|
| Kits (`/kits/`, `/kits/[id]/`, home cards) | `hardware/kits/*.toml` | `glob` collection + `kitSchema` |
| Model numbers (coldest water, power, room table) | `software/opod` | `python -m opod.site_data` → `src/data/model.json` (committed) |
| Parts catalog (`/parts/`, counts) | `hardware/parts.toml` | `file` collection, roles unwrapped |
| Capability table (`/features/`) | `docs/FEATURES.md` | `src/lib/features.ts` parser + `src/data/feature-names.yaml` |
| Rendered docs (`/docs/…`) | SAFETY, CONTRIBUTING, CODE_OF_CONDUCT, `docs/design/0*.md`, `hardware/WIRING.md` | `glob` collection; relative links rewritten by `src/lib/remark-repo-links.ts` |
| Schedule curve (hero, `/schedule/`) | `opod.schedule.DEFAULT` via `model.json` | TS port `src/lib/schedule.ts`, tested against `hub/.../test/schedule.txt` |
| Status, help wanted, sponsor asks | `src/data/*.yaml` | hand-maintained, each entry with a `source` |
| Issue templates | `.github/ISSUE_TEMPLATE/*.yml` | `glob` collection |

## Owner decisions (all in `src/site.ts`)

- **Domain:** `https://openbedclimate.moinsen.dev`. `SITE_URL` env overrides it in `astro.config.mjs`; also in `public/robots.txt`.
  Cloudflare Pages project: `open-bed-climate` (build `npm ci && npm run build`, output `dist`, root `website`).
- **Repo:** `https://github.com/moinsen-dev/open-bed-climate`. Discussions and issue-template links derive from it.
- **Contact:** `business@moinsen.dev`. Sponsorship is by e-mail for now (`SPONSOR_MAILTO`, subject "Open Bed Climate sponsorship").
  GitHub Sponsors or Open Collective may come later.
- **Legal:** the Impressum and the full privacy policy live on moinsen.dev. `/impressum/` is a 301 to
  `https://www.moinsen.dev/en/impressum` (`public/_redirects`). `/privacy/` is a short site-specific supplement that links to
  `https://www.moinsen.dev/en/privacy`.
- **Site content licence:** Apache-2.0 unless noted, consistent with the repo docs.
- **Not set up:** newsletter (`NEWSLETTER_URL` is null, so no form is shown).

The guard fails the build if "TBD" appears in any built page's visible text, so a placeholder can't ship.

## Decisions

Where the plans conflict or didn't survive contact with the toolchain:

1. **Markdown pipeline.** Astro 7 uses Sätteri, not remark, by default. The repo-link rewriter is a Sätteri mdast plugin
   (`@astrojs/markdown-satteri` pinned 0.4.2) instead of a remark plugin. `syntaxHighlight: false`, because Shiki emits
   inline `style=""`, which the CSP and the guard forbid. Code blocks are styled in CSS.
2. **JS budget.** 03-tech allowed 0 KB on most pages, but 04-design needs a theme toggle on every page and the hero
   island on `/`. Budget: ≤ 1 KB gz everywhere (`public/theme-init.js`, external and synchronous so it is CSP-safe),
   ≤ 7 KB on `/`, ≤ 15 KB on `/kits/` and `/schedule/`. Actual: about 0.6 / 2.5 / 1.2 / 3.6 KB.
3. **Fonts.** There are three families (Bricolage Grotesque, Inter, JetBrains Mono), as in DESIGN.md, so the font budget is 3 files rather than 2.
   The `@font-face` rules are hand-written in `tokens.css` against the Latin `wght` woff2 files only (the Fontsource index CSS would pull in every subset).
4. **Storage.** The plans say "no storage", but the design has a theme toggle. Resolution: the theme follows `prefers-color-scheme`, and it is persisted
   to `localStorage` only after an explicit click. This is disclosed on `/privacy/`. The phase banner is **not dismissible**, so it needs no JS and no storage.
5. **Footer wording.** 01-content's generic "any bed-cooling manufacturer" is used site-wide, not 02's "Eight Sleep".
   The guard allows "Eight Sleep" only on `/about/` and on repo docs rendered verbatim under `/docs/`, because the design docs mention it.
6. **Docs scope.** `docs/design/OPEN-DECISIONS.md` (has the off-site section, C8) and `BOM.md` (stale 12 V / prices, C2/C3)
   are not rendered in place. They link to the repo. `/status/` shows the decided items D1–D3 and the five measurements.
7. **FEATURES.md.** The table has 21 rows, so `feature-names.yaml` has 21 entries. Rows 0, 2, 8 and 13 override the
   approach cell. Row 2 contains "Pod 6" (C6), and row 0 carries the C9 setpoint wording. The Module column's plug emoji is rendered as "Third-party".
8. **Copy and routes.** 01-content wins over the 04-design wireframes for the H1, the CTAs, the nav and `/contribute/` (not `/get-involved`).
   Sponsor tiers come from 02-community and are labelled "proposed". The funding buckets use `<meter>` at 0 %, because a `style=` width is not allowed under the CSP.
9. **Schema.** `parts.toml` uses `""` for `source` / `verified_on` on unverified examples. The Zod schema accepts `""` there
   and still requires both fields for `datasheet` / `listing`.
10. **Content collections order.** Astro's `file()` loader sorts by id. Pages restore YAML order with `src/lib/file-order.ts`.
11. **Link check** uses `--skip "^https?://(?!localhost|127\.0\.0\.1)"`. The plan's pattern skipped the local server, so it scanned 0 links.
12. **Temperature colors.** These are computed by `tempColor()` (OKLab interpolation, which avoids a green sweep between cyan and amber).
    Text uses generated classes `tc-13…tc-43` (`temp-scale.css`), never inline styles. In Dawn, text switches to dawn-cold / dawn-warm, and the hero water strokes are darkened.
    The Dawn `hairline` (`#D3D8E2`) is not in DESIGN.md and is decorative only.
13. **Not built (yet).** These items are left out:
    - I3, the exploded-kit illustration. Kits shows the module map instead.
    - The `/builds/` gallery, because there are no build TOMLs yet.
    - `VideoEmbed` and `NewsletterForm`, because there is no video and no listmonk yet.
    - Sponsor logos via `image()`. The sponsors list is text-only.
    - Contributor avatars. `.all-contributorsrc` doesn't exist, and the GitHub API fallback is skipped while the repo URL is a placeholder.
    - Hand-written copy lives in the `.astro` pages rather than `src/content/copy/`.
14. **Legal pages are external.** The 02-community plan wanted an on-site Impressum and privacy page. The owner decided to use
    the moinsen.dev pages instead. The outbound links are plain `<a href>` links, which the guard allows because they are not requests.
15. **Repo data issues found** (not fixed here). Two example-part links in `hardware/parts.toml` are dead: china.org.ru (403)
    and the Espressif ESP32-S3-DevKitC user-guide URL (404).
