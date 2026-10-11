// Shared geometry for the night-curve charts (hero strip, schedule editor). Pure functions: used at build time to
// render the static SVG and in the islands to redraw it, so both always agree.
import { setpoint, type Schedule } from "./schedule.ts";

export interface Frame {
  w: number;
  h: number;
  left: number;
  right: number;
  top: number;
  bottom: number;
  minEnd: number; // minutes shown on the x axis
  cMin: number; // °C at the bottom
  cMax: number; // °C at the top
}

export const xOf = (f: Frame, minute: number) => f.left + ((f.w - f.left - f.right) * minute) / f.minEnd;
export const yOf = (f: Frame, c: number) => f.top + ((f.h - f.top - f.bottom) * (f.cMax - c)) / (f.cMax - f.cMin);
export const minuteOf = (f: Frame, x: number) => ((x - f.left) / (f.w - f.left - f.right)) * f.minEnd;
export const cOf = (f: Frame, y: number) => f.cMax - ((y - f.top) / (f.h - f.top - f.bottom)) * (f.cMax - f.cMin);

/** SVG path of the setpoint curve; the part after wake (side off) is returned separately. */
export function curvePath(f: Frame, s: Schedule, wakeMinute: number | null, offsetC = 0, step = 2): { on: string; lastOn: [number, number] | null } {
  const parts: string[] = [];
  let last: [number, number] | null = null;
  for (let m = 0; m <= f.minEnd; m += step) {
    const c = setpoint(s, m, wakeMinute);
    if (c === null) break;
    const pt: [number, number] = [xOf(f, m), yOf(f, c + offsetC)];
    parts.push(`${parts.length ? "L" : "M"}${pt[0].toFixed(1)} ${pt[1].toFixed(1)}`);
    last = pt;
  }
  return { on: parts.join(" "), lastOn: last };
}
