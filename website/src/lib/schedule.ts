// Port of software/opod/src/opod/schedule.py. Tested against the same golden vectors as the C++ hub port
// (hub/esphome/components/opod/test/schedule.txt), see test/schedule.test.ts.

export type Point = [minute: number, celsius: number];
export interface Schedule {
  points: Point[];
  wake_ramp_min: number;
  wake_target_c: number;
}
export interface Limits {
  setpoint_min_c: number;
  setpoint_max_c: number;
}

export function base(points: Point[], minute: number): number {
  if (minute <= points[0][0]) return points[0][1];
  for (let k = 0; k < points.length - 1; k++) {
    const [m0, c0] = points[k];
    const [m1, c1] = points[k + 1];
    if (minute <= m1) return c0 + ((c1 - c0) * (minute - m0)) / (m1 - m0);
  }
  return points[points.length - 1][1];
}

/** Setpoint `minute` after bedtime; null once past the wake time (the side turns off). */
export function setpoint(s: Schedule, minute: number, wakeMinute: number | null): number | null {
  if (wakeMinute !== null) {
    if (minute >= wakeMinute) return null;
    const rampStart = wakeMinute - s.wake_ramp_min;
    if (minute > rampStart) {
      const b = base(s.points, rampStart);
      const frac = (minute - rampStart) / s.wake_ramp_min;
      return b + (s.wake_target_c - b) * frac;
    }
  }
  return base(s.points, minute);
}

/** Minutes from a start time of day to the next wake time of day (minutes since midnight), in 1..1440. */
export function wakeOffset(startMinOfDay: number, wakeMinOfDay: number): number {
  const d = (((wakeMinOfDay - startMinOfDay) % 1440) + 1440) % 1440;
  return d || 1440;
}

/** Same rules as Schedule.__post_init__. Returns an error message, or null when valid. */
export function validate(points: Point[], limits: Limits): string | null {
  if (points.length === 0) return "schedule needs at least one point";
  for (let k = 1; k < points.length; k++) if (points[k][0] < points[k - 1][0]) return "points must be sorted by time";
  for (const [, c] of points)
    if (c < limits.setpoint_min_c || c > limits.setpoint_max_c)
      return `setpoint ${c} outside ${limits.setpoint_min_c}..${limits.setpoint_max_c}`;
  return null;
}

/** Sample the curve for drawing: one value per `step` minutes from 0 to `end`. Null = off after wake. */
export function sample(s: Schedule, end: number, wakeMinute: number | null, step = 2): [number, number | null][] {
  const out: [number, number | null][] = [];
  for (let m = 0; m <= end; m += step) out.push([m, setpoint(s, m, wakeMinute)]);
  if (out[out.length - 1][0] !== end) out.push([end, setpoint(s, end, wakeMinute)]);
  return out;
}

export const clockLabel = (minOfDay: number) => {
  const m = ((Math.round(minOfDay) % 1440) + 1440) % 1440;
  return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
};
