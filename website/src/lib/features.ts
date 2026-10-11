import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { Loader } from "astro/loaders";
import { FEATURE_STATE, type FeatureState } from "./schemas.ts";

export interface FeatureRow {
  row: number;
  pod: string;
  approach: string;
  module: string;
  status: { state: FeatureState; note: string }[];
}

const EMOJI = Object.keys(FEATURE_STATE) as (keyof typeof FEATURE_STATE)[];

function splitCells(line: string): string[] {
  const cells = line.trim().replace(/^\|/, "").replace(/\|$/, "").split(/(?<!\\)\|/);
  return cells.map((c) => c.trim().replace(/\\\|/g, "|"));
}

function parseStatus(cell: string): FeatureRow["status"] {
  return cell.split(",").map((part) => {
    const p = part.trim();
    const emoji = EMOJI.find((e) => p.startsWith(e));
    if (!emoji) throw new Error(`FEATURES.md: unknown status "${p}"`);
    return { state: FEATURE_STATE[emoji], note: p.slice(emoji.length).trim() };
  });
}

/** Parse the capability table out of docs/FEATURES.md. Throws on any malformed row so a bad edit breaks the build. */
export function parseFeatureTable(md: string): FeatureRow[] {
  const lines = md.split("\n");
  const start = lines.findIndex((l) => /^\|\s*Pod 6 feature/.test(l));
  if (start < 0) throw new Error("FEATURES.md: feature table header not found");
  const rows: FeatureRow[] = [];
  for (let i = start + 2; i < lines.length && lines[i].trim().startsWith("|"); i++) {
    const cells = splitCells(lines[i]);
    if (cells.length !== 4) throw new Error(`FEATURES.md line ${i + 1}: expected 4 columns, got ${cells.length}`);
    const [pod, approach, module, status] = cells;
    rows.push({ row: rows.length, pod, approach, module, status: parseStatus(status) });
  }
  return rows;
}

export const featuresLoader = (path: string): Loader => ({
  name: "features-md",
  load: async ({ store, parseData, renderMarkdown, watcher }) => {
    const abs = resolve(path);
    const rows = parseFeatureTable(await readFile(abs, "utf8"));
    store.clear();
    for (const row of rows) {
      const id = String(row.row);
      const data = await parseData({ id, data: { ...row } });
      store.set({ id, data, rendered: await renderMarkdown(row.approach) });
    }
    watcher?.add(abs);
  },
});
