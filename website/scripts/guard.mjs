// Post-build content + CSP guard (03-tech §4). Scans dist/ and fails on:
// - banned wording: "Pod-class" anywhere; "Open Pod" (old name) anywhere; "Eight Sleep" outside the allowed pages
// - emoji inside a .status element
// - inline <script> without src, or any style="" attribute (CSP: script-src/style-src 'self')
// - any third-party request on page load (resource-loading elements/attributes, CSS url()/@import)
// - <iframe> in built HTML (videos are click-to-load only)
// - a visible "TBD" placeholder anywhere (every owner decision must be filled in before deploy)
// Plain <a href> links to other sites are allowed: they are not requests until clicked.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const DIST = new URL("../dist/", import.meta.url).pathname;
// Nominative mention: at most once on /about/ and /features/ (honesty rule H5); repo docs rendered verbatim under
// /docs/ keep their own wording.
const EIGHT_SLEEP_ONCE = [/^about\//, /^features\//];
const EIGHT_SLEEP_VERBATIM = [/^docs\//];
const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B50}\u{2705}\u{274C}]/u;

const walk = (dir) =>
  readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
const files = walk(DIST);
const errors = [];
const fail = (file, msg) => errors.push(`${relative(DIST, file)}: ${msg}`);
const isExternal = (url) => /^(https?:)?\/\//i.test(url.trim());

for (const file of files.filter((f) => f.endsWith(".html"))) {
  const rel = relative(DIST, file);
  const html = readFileSync(file, "utf8");
  const text = html.replace(/<script[\s\S]*?<\/script>/g, "").replace(/<[^>]+>/g, " ");

  if (/\bTBD\b/.test(text)) fail(file, '"TBD" placeholder in visible text');
  if (/Pod-class/i.test(text)) fail(file, 'banned wording "Pod-class"');
  if (/Open\s+Pod\b/i.test(text)) fail(file, 'old project name "Open Pod"');
  const es = (text.match(/Eight Sleep/gi) ?? []).length;
  if (es && !EIGHT_SLEEP_VERBATIM.some((re) => re.test(rel))) {
    if (!EIGHT_SLEEP_ONCE.some((re) => re.test(rel))) fail(file, '"Eight Sleep" outside allowed pages');
    else if (es > 1) fail(file, `"Eight Sleep" named ${es} times (max 1)`);
  }

  for (const m of html.matchAll(/<(\w+)[^>]*class="[^"]*\bstatus\b[^"]*"[^>]*>([\s\S]*?)<\/\1>/g)) {
    if (EMOJI.test(m[2])) fail(file, `emoji in status label: ${m[2].trim().slice(0, 40)}`);
  }
  for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)) {
    if (!/\bsrc=/.test(m[1]) && !/type="application\/(ld\+)?json"/.test(m[1])) fail(file, "inline <script> (CSP)");
  }
  if (/\sstyle\s*=\s*["']/i.test(html)) fail(file, 'style="" attribute (CSP)');
  if (/<style\b/i.test(html)) fail(file, "inline <style> element (CSP)");
  if (/<iframe\b/i.test(html)) fail(file, "<iframe> in built HTML (use click-to-load)");
  if (/<(object|embed)\b/i.test(html)) fail(file, "<object>/<embed>");

  for (const m of html.matchAll(/<(script|img|source|video|audio|link|iframe|track)\b([^>]*)>/gi)) {
    const [, tag, attrs] = m;
    if (tag.toLowerCase() === "link") {
      const rel = /\brel="([^"]*)"/i.exec(attrs)?.[1] ?? "";
      if (/\b(canonical|alternate)\b/i.test(rel)) continue;
    }
    for (const a of attrs.matchAll(/\b(src|href|poster|srcset|data)="([^"]*)"/gi)) {
      const urls = a[1].toLowerCase() === "srcset" ? a[2].split(",").map((s) => s.trim().split(/\s+/)[0]) : [a[2]];
      for (const u of urls) if (isExternal(u)) fail(file, `third-party request: <${tag} ${a[1]}="${u}">`);
    }
  }
  if (/avatars\.githubusercontent\.com/.test(html)) fail(file, "hotlinked GitHub avatar");
}

for (const file of files.filter((f) => f.endsWith(".css"))) {
  const css = readFileSync(file, "utf8");
  for (const m of css.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)) if (isExternal(m[1])) fail(file, `third-party url(): ${m[1]}`);
  for (const m of css.matchAll(/@import\s+(?:url\()?["']?([^"');]+)/g)) if (isExternal(m[1])) fail(file, `third-party @import: ${m[1]}`);
}

// Shopping pages: the rendered grand total must equal the total line opod.shopping wrote into the .md.
for (const file of files.filter((f) => /kits\/[^/]+\/shopping\/index\.html$/.test(relative(DIST, f)))) {
  const kit = relative(DIST, file).split("/")[1];
  const shown = /data-shopping-total="([\d.]+)"/.exec(readFileSync(file, "utf8"))?.[1];
  const mdPath = new URL(`../../hardware/shopping/${kit}.md`, import.meta.url);
  const md = readFileSync(mdPath, "utf8");
  const want = /\*\*Total \(bench \+ bed\)\*\*\s*\|\s*\*\*([\d,.]+)\*\*/.exec(md)?.[1]?.replace(/,/g, "");
  if (!shown || !want || Number(shown).toFixed(2) !== Number(want).toFixed(2)) fail(file, `shopping total ${shown} != ${kit}.md total ${want}`);
}

if (errors.length) {
  console.error(`guard: ${errors.length} problem(s)\n` + errors.map((e) => "  - " + e).join("\n"));
  process.exit(1);
}
console.log(`guard: ${files.filter((f) => f.endsWith(".html")).length} pages clean (wording, CSP, no third-party requests)`);
