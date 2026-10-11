// Generates src/styles/temp-scale.css: one text-color class per whole °C (13–43) from lib/temp.ts.
// Text colors come from classes, never style="" attributes (CSP style-src 'self').
// On Dawn the mid-tone stops fail contrast on paper, so text switches to dawn-cold / dawn-warm (DESIGN.md).
// Usage: node scripts/gen-temp-css.mjs   (test/data.test.ts checks it is up to date)
import { writeFileSync } from "node:fs";
import { tempCss } from "../src/lib/temp.ts";
writeFileSync(new URL("../src/styles/temp-scale.css", import.meta.url), tempCss());
