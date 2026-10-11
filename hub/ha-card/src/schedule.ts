// Night curve: port of software/opod/src/opod/schedule.py (and hub/esphome/components/opod/schedule.h).
// Tested against the same golden vectors (hub/esphome/components/opod/test/schedule.txt).

/** (minutes after bedtime, °C), sorted by time. */
export type Point = readonly [number, number];

export interface Schedule {
  points: readonly Point[];
  wakeRampMin: number;
  wakeTargetC: number;
}

/** Same as opod.schedule.DEFAULT and the default `points` in opod-hub-common.yaml. */
export const DEFAULT_SCHEDULE: Schedule = {
  points: [
    [0, 24],
    [30, 21],
    [120, 20],
    [300, 23],
    [420, 25],
  ],
  wakeRampMin: 30,
  wakeTargetC: 32,
};

/** The curve without the wake ramp: linear between points, held at the ends. */
export function base(s: Schedule, minute: number): number {
  const pts = s.points;
  if (minute <= pts[0][0]) return pts[0][1];
  for (let i = 1; i < pts.length; i++) {
    const [m0, c0] = pts[i - 1];
    const [m1, c1] = pts[i];
    if (minute <= m1) return c0 + ((c1 - c0) * (minute - m0)) / (m1 - m0);
  }
  return pts[pts.length - 1][1];
}

/** Setpoint `minute` after bedtime; null once past the wake time (the side turns off). */
export function setpoint(s: Schedule, minute: number, wakeMinute: number | null = null): number | null {
  if (wakeMinute !== null) {
    if (minute >= wakeMinute) return null;
    const rampStart = wakeMinute - s.wakeRampMin;
    if (minute > rampStart) {
      const b = base(s, rampStart);
      return b + ((s.wakeTargetC - b) * (minute - rampStart)) / s.wakeRampMin;
    }
  }
  return base(s, minute);
}

/** Minutes from a start time of day to the next wake time of day (minutes since midnight), in 1..1440. */
export function wakeOffset(startMinOfDay: number, wakeMinOfDay: number): number {
  const d = (((wakeMinOfDay - startMinOfDay) % 1440) + 1440) % 1440;
  return d || 1440;
}

/** Points written like the ESPHome config: `{ at: 30min, temperature: 21 }`, or `[30, 21]`. */
export type PointInput = readonly [number, number] | { at: number | string; temperature: number };

/** Minutes from a number (minutes) or an ESPHome-style duration ("30min", "2h", "90s", "1h30min"). */
export function parseMinutes(v: number | string): number {
  if (typeof v === "number") return v;
  const s = v.trim();
  if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s);
  const re = /(\d+(?:\.\d+)?)\s*(h|min|s)/g;
  let total = 0;
  let consumed = "";
  for (let m = re.exec(s); m; m = re.exec(s)) {
    total += Number(m[1]) * (m[2] === "h" ? 60 : m[2] === "min" ? 1 : 1 / 60);
    consumed += m[0];
  }
  if (!consumed || consumed.replace(/\s/g, "") !== s.replace(/\s/g, "")) {
    throw new Error(`cannot read duration "${v}" (use minutes, or e.g. 30min / 2h)`);
  }
  return total;
}

/** Build a schedule from card config; throws with a readable message on bad input (shown by HA as a card error). */
export function scheduleFromConfig(
  points: readonly PointInput[] | undefined,
  wakeRamp: number | string | undefined,
  wakeTemperature: number | undefined,
): Schedule {
  const pts: Point[] = points?.length
    ? points.map((p) => (Array.isArray(p) ? [Number(p[0]), Number(p[1])] : [parseMinutes((p as { at: number | string }).at), Number((p as { temperature: number }).temperature)]))
    : [...DEFAULT_SCHEDULE.points];
  for (let i = 0; i < pts.length; i++) {
    const [m, c] = pts[i];
    if (!Number.isFinite(m) || !Number.isFinite(c)) throw new Error(`points[${i}] is not a number pair`);
    if (i > 0 && m <= pts[i - 1][0]) throw new Error("points must be sorted by time, without duplicates");
  }
  return {
    points: pts,
    wakeRampMin: wakeRamp === undefined ? DEFAULT_SCHEDULE.wakeRampMin : parseMinutes(wakeRamp),
    wakeTargetC: wakeTemperature ?? DEFAULT_SCHEDULE.wakeTargetC,
  };
}

/** Samples of the night for a sparkline: every `step` minutes from bedtime to the wake time (or the last point + 1 h). */
export function sampleNight(s: Schedule, wakeMinute: number | null, step = 5): Point[] {
  const end = wakeMinute ?? s.points[s.points.length - 1][0] + 60;
  const out: Point[] = [];
  for (let m = 0; m < end; m += step) out.push([m, setpoint(s, m, wakeMinute) as number]);
  // Last sample just before the side turns off, so the ramp reaches the wake temperature.
  const last = wakeMinute === null ? end : end - 1e-6;
  out.push([end, setpoint(s, last, wakeMinute) as number]);
  return out;
}
