// The release ships exactly one file; it must not import anything at runtime (Home Assistant serves it as-is).
import { readdirSync, readFileSync } from "node:fs";

const files = readdirSync("dist");
if (files.length !== 1 || files[0] !== "open-bed-climate-card.js") {
  console.error(`dist/ must hold only open-bed-climate-card.js, found: ${files.join(", ")}`);
  process.exit(1);
}
const js = readFileSync("dist/open-bed-climate-card.js", "utf8");
if (/\bimport\s*(?:[\w{}*\s,]+from\s*)?["']|\bimport\s*\(/.test(js)) {
  console.error("dist/open-bed-climate-card.js contains a runtime import");
  process.exit(1);
}
console.log(`dist/open-bed-climate-card.js: ${(js.length / 1024).toFixed(1)} KiB, self-contained`);
