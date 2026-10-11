// "Site data matches repo": every kit TOML passes the site schema, model.json is in step with the kits,
// the parts catalog is valid, and feature-names.yaml has one name per FEATURES.md row.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { parse } from "smol-toml";
import { kitSchema, partRoleSchema } from "../src/lib/schemas.ts";
import { parseFeatureTable } from "../src/lib/features.ts";
import { tempCss } from "../src/lib/temp.ts";
import model from "../src/data/model.json" with { type: "json" };

const repo = (p: string) => new URL(`../../${p}`, import.meta.url);
const kitFiles = readdirSync(repo("hardware/kits")).filter((f) => f.endsWith(".toml"));

test("kit TOMLs pass the schema and match model.json", () => {
  const ids = new Set<string>();
  for (const f of kitFiles) {
    const id = f.replace(/\.toml$/, "");
    ids.add(id);
    const kit = kitSchema.parse(parse(readFileSync(repo(`hardware/kits/${f}`), "utf8")));
    const m = (model.kits as Record<string, (typeof model.kits)["solo-starter"]>)[id];
    assert.ok(m, `model.json lacks ${id}: run npm run data`);
    assert.equal(m.name, kit.kit.name);
    assert.ok(kit.claims.min_water_c >= m.check.min_water_c - 0.1, `${id}: claim beats the model`);
    assert.deepEqual(m.check.problems, []);
    const at25 = m.coldest_by_room.find((r) => r.room_c === 25);
    assert.equal(at25?.water_c, m.check.min_water_c, `${id}: coldest_by_room[25] != check`);
  }
  assert.deepEqual([...ids].sort(), Object.keys(model.kits).sort());
});

test("parts.toml passes the schema with unique role ids", () => {
  const roles = (parse(readFileSync(repo("hardware/parts.toml"), "utf8")) as { role: unknown[] }).role;
  const parsed = roles.map((r) => partRoleSchema.parse(r));
  assert.equal(new Set(parsed.map((r) => r.id)).size, parsed.length);
});

test("feature-names.yaml has one entry per FEATURES.md row", () => {
  const rows = parseFeatureTable(readFileSync(repo("docs/FEATURES.md"), "utf8"));
  const yaml = readFileSync(new URL("../src/data/feature-names.yaml", import.meta.url), "utf8");
  const names = [...yaml.matchAll(/^\s+row:\s*(\d+)\s*$/gm)].map((m) => Number(m[1]));
  assert.deepEqual(names, rows.map((r) => r.row));
});

test("temp-scale.css is up to date", () => {
  const css = readFileSync(new URL("../src/styles/temp-scale.css", import.meta.url), "utf8");
  assert.equal(css, tempCss(), "run: node scripts/gen-temp-css.mjs");
});
