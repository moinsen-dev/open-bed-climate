import { readFileSync } from "node:fs";

// Astro's file() loader returns entries sorted by id. Hand-maintained YAML lists are ordered on purpose
// (priority, chronology), so pages restore the order of `- id:` lines in the source file.
export function inFileOrder<T extends { id: string }>(entries: T[], path: string): T[] {
  const ids = [...readFileSync(path, "utf8").matchAll(/^- id:\s*["']?([^"'\s]+)/gm)].map((m) => m[1]);
  const rank = new Map(ids.map((id, i) => [id, i]));
  return [...entries].sort((a, b) => (rank.get(a.id) ?? 1e9) - (rank.get(b.id) ?? 1e9));
}
