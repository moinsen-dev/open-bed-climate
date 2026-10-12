import type { Schedule } from "./schedule.ts";

const num = (x: number) => String(Math.round(x * 10) / 10);

/** The schedule block of hub/esphome/obc-hub.yaml (switch platform obc) for a given curve. */
export function hubYaml(s: Schedule): string {
  const lines = ["    points:"];
  for (const [m, c] of s.points) lines.push(`      - { at: ${num(m)}min, temperature: ${num(c)} }`);
  lines.push(`    wake_ramp: ${num(s.wake_ramp_min)}min`);
  lines.push(`    wake_temperature: ${num(s.wake_target_c)}`);
  return lines.join("\n");
}
