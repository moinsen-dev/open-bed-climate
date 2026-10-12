// Shopping lists (hardware/shopping/*.toml): parsing and totals. Same arithmetic as obc.shopping (line = qty × unit;
// totals = bench + bed; tools are not counted). test/shopping.test.ts checks it against the Python-rendered Markdown.
import { readFileSync } from "node:fs";
import { parse } from "smol-toml";
import { shoppingSchema, type ShoppingData } from "./schemas.ts";

export type ShoppingItem = ShoppingData["item"][number];

export const STAGE_TITLE = {
  bench: "Stage 1: bench build",
  bed: "Stage 2: bed",
  tool: "Tools",
} as const;
export const STAGE_NOTE = {
  bench: "Everything for the bench build: no bed, a 10 l water container as the thermal load.",
  bed: "Added when you move from the bench to the bed.",
  tool: "Not in the totals; qty 0 means you probably own it already.",
} as const;

export const lineEur = (i: ShoppingItem) => i.qty * i.unit_eur;

export function loadShopping(path: string | URL): ShoppingData {
  return shoppingSchema.parse(parse(readFileSync(path, "utf8")));
}

export function totals(d: ShoppingData) {
  const sub = (stage: string) => d.item.filter((i) => i.stage === stage).reduce((a, i) => a + lineEur(i), 0);
  const bench = sub("bench");
  const bed = sub("bed");
  return {
    bench,
    bed,
    total: bench + bed,
    estimates: d.item.filter((i) => i.status === "estimate" && i.stage !== "tool").length,
  };
}

/** 1,345.76 (same format as Python's f"{x:,.2f}"). */
export const eur = (x: number) =>
  x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
