// Shopping lists: the site's totals equal the sum over the TOML lines, and match the total line that
// opod.shopping rendered into hardware/shopping/<kit>.md (the same numbers as the Python reference).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { parse } from "smol-toml";
import { loadShopping, totals, eur } from "../src/lib/shopping.ts";

const dir = new URL("../../hardware/shopping/", import.meta.url);
const lists = readdirSync(dir).filter((f) => f.endsWith(".toml"));

test("there is at least one shopping list", () => assert.ok(lists.length >= 1));

for (const f of lists) {
  test(`${f}: totals match the raw TOML and the Python-rendered Markdown`, () => {
    const data = loadShopping(new URL(f, dir));
    const t = totals(data);
    const raw = parse(readFileSync(new URL(f, dir), "utf8")) as { item: { qty: number; unit_eur: number; stage: string }[] };
    const sum = (stage: string) => raw.item.filter((i) => i.stage === stage).reduce((a, i) => a + i.qty * i.unit_eur, 0);
    assert.ok(Math.abs(t.bench - sum("bench")) < 1e-9);
    assert.ok(Math.abs(t.bed - sum("bed")) < 1e-9);
    assert.ok(Math.abs(t.total - (sum("bench") + sum("bed"))) < 1e-9);
    const md = readFileSync(new URL(f.replace(/\.toml$/, ".md"), dir), "utf8");
    const line = /\|\s*\*\*Total \(bench \+ bed\)\*\*\s*\|\s*\*\*([\d,.]+)\*\*\s*\|/.exec(md);
    assert.ok(line, "total line not found in the rendered .md (run: python -m opod.shopping)");
    assert.equal(eur(t.total), line[1]);
    assert.match(md, new RegExp(`Subtotal stage 1 \\(bench\\) \\| ${eur(t.bench).replace(/[.]/g, "\\.")} \\|`));
  });
}

test("eur() formats like Python's {:,.2f}", () => {
  assert.equal(eur(1345.76), "1,345.76");
  assert.equal(eur(5), "5.00");
});
