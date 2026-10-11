// Byte budget (hard gate, 03-tech §4). Per page: gzip size of the referenced JS and CSS, the HTML itself and the
// number of font files. Deterministic, unlike Lighthouse.
//
// JS limits deviate from 03-tech on purpose (see README "Decisions"): every page loads the tiny theme script
// (/theme-init.js, ≤ 1 KB gz), the home page adds the hero animation, /kits/ and /schedule/ their islands,
// /install/ the firmware install button.
import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join, relative } from "node:path";
import { gzipSync } from "node:zlib";

const DIST = new URL("../dist/", import.meta.url).pathname;
const KB = 1024;
// /install/: the ESP Web Tools button; its install dialog and flasher load only after a click (not counted here).
const JS_LIMIT = { "index.html": 7 * KB, "kits/index.html": 15 * KB, "schedule/index.html": 15 * KB, "install/index.html": 4 * KB };
const JS_DEFAULT = 1 * KB; // theme script only
const CSS_TOTAL = 20 * KB;
const HTML_LIMIT = 60 * KB;
const FONT_FILES = 3; // display + body + mono (DESIGN.md typography); 03-tech said 2 with a system mono

const walk = (dir) => readdirSync(dir).flatMap((f) => (statSync(join(dir, f)).isDirectory() ? walk(join(dir, f)) : [join(dir, f)]));
const gz = (p) => gzipSync(readFileSync(p)).length;
const local = (u) => join(DIST, u.replace(/^\//, "").split(/[?#]/)[0]);
const errors = [];
const cssSeen = new Map();
const rows = [];

for (const file of walk(DIST).filter((f) => f.endsWith(".html"))) {
  const rel = relative(DIST, file);
  const html = readFileSync(file, "utf8");
  let js = 0;
  const jsFiles = new Set();
  for (const m of html.matchAll(/<script\b[^>]*\bsrc="(\/[^"]+)"/g)) jsFiles.add(m[1]);
  // Follow static imports of bundled modules (Astro hoists shared chunks).
  const queue = [...jsFiles];
  while (queue.length) {
    const u = queue.pop();
    const p = local(u);
    if (!existsSync(p)) continue;
    const src = readFileSync(p, "utf8");
    for (const m of src.matchAll(/(?:import|from)\s*["'](\.{0,2}\/[^"']+\.js)["']/g)) {
      const next = new URL(m[1], "http://x" + u).pathname;
      if (!jsFiles.has(next)) { jsFiles.add(next); queue.push(next); }
    }
  }
  for (const u of jsFiles) if (existsSync(local(u))) js += gz(local(u));
  for (const m of html.matchAll(/<link\b[^>]*rel="stylesheet"[^>]*href="(\/[^"]+)"/g)) {
    if (existsSync(local(m[1]))) cssSeen.set(m[1], gz(local(m[1])));
  }
  const fonts = new Set([...html.matchAll(/href="(\/[^"]+\.woff2)"/g)].map((m) => m[1]));
  // Fonts referenced from CSS count for every page (all three faces are used sitewide).
  const htmlGz = gzipSync(html).length;
  const jsLimit = JS_LIMIT[rel] ?? JS_DEFAULT;
  if (js > jsLimit) errors.push(`${rel}: JS ${(js / KB).toFixed(1)} KB gz > ${(jsLimit / KB).toFixed(1)} KB`);
  if (htmlGz > HTML_LIMIT) errors.push(`${rel}: HTML ${(htmlGz / KB).toFixed(1)} KB gz > 60 KB`);
  if (fonts.size > FONT_FILES) errors.push(`${rel}: ${fonts.size} preloaded font files > ${FONT_FILES}`);
  rows.push([rel, js, htmlGz]);
}
const fontFaces = [...new Set([...cssSeen.keys()].flatMap((u) => [...readFileSync(local(u), "utf8").matchAll(/url\(([^)]+\.woff2)\)/g)].map((m) => m[1])))];
if (fontFaces.length > FONT_FILES) errors.push(`${fontFaces.length} font files in CSS > ${FONT_FILES}`);
const cssTotal = [...cssSeen.values()].reduce((a, b) => a + b, 0);
if (cssTotal > CSS_TOTAL) errors.push(`CSS total ${(cssTotal / KB).toFixed(1)} KB gz > 20 KB`);

const maxJs = rows.reduce((a, r) => (r[1] > a[1] ? r : a), ["", 0]);
console.log(`budget: ${rows.length} pages · CSS ${(cssTotal / KB).toFixed(1)} KB gz · fonts ${fontFaces.length} · max JS ${(maxJs[1] / KB).toFixed(1)} KB gz (${maxJs[0]})`);
for (const r of rows.filter((r) => r[1] > JS_DEFAULT || r[0] === "index.html")) console.log(`  ${r[0]}: JS ${(r[1] / KB).toFixed(1)} KB gz, HTML ${(r[2] / KB).toFixed(1)} KB gz`);
if (errors.length) {
  console.error("budget exceeded:\n" + errors.map((e) => "  - " + e).join("\n"));
  process.exit(1);
}
