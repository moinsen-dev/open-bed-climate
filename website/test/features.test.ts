import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseFeatureTable } from "../src/lib/features.ts";

const md = readFileSync(new URL("../../docs/FEATURES.md", import.meta.url), "utf8");

test("FEATURES.md parses into known states", () => {
  const rows = parseFeatureTable(md);
  assert.ok(rows.length >= 15, `only ${rows.length} rows`);
  for (const r of rows) {
    assert.ok(r.status.length >= 1);
    for (const s of r.status) assert.ok(["now", "planned", "third_party", "out_of_scope"].includes(s.state));
  }
  const schedule = rows.find((r) => r.pod.startsWith("Temperature schedule"));
  assert.deepEqual(schedule?.status, [{ state: "now", note: "basic" }, { state: "planned", note: "adaptive" }]);
});

test("a malformed table throws", () => {
  const bad = readFileSync(new URL("./fixtures/features-bad.md", import.meta.url), "utf8");
  assert.throws(() => parseFeatureTable(bad), /unknown status|expected 4 columns/);
});

test("a table with a missing column throws", () => {
  assert.throws(() => parseFeatureTable("| Pod 6 feature | a | b | c |\n|---|---|---|---|\n| x | y | ✅ |\n"), /expected 4 columns/);
});
