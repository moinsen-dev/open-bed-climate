import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  DEFAULT_SCHEDULE,
  parseMinutes,
  sampleNight,
  scheduleFromConfig,
  setpoint,
  wakeOffset,
  type Point,
  type Schedule,
} from "../src/schedule";

// Golden vectors from the Python reference (python -m opod.golden), shared with the C++ port in the hub component.
const VECTORS = fileURLToPath(new URL("../../esphome/components/opod/test/schedule.txt", import.meta.url));

describe("schedule port matches opod.schedule (golden vectors)", () => {
  it("passes every S and W vector", () => {
    let sched: Schedule = DEFAULT_SCHEDULE;
    let checked = 0;
    const failures: string[] = [];
    for (const line of readFileSync(VECTORS, "utf8").split("\n")) {
      if (!line.trim() || line.startsWith("#")) continue;
      const [kind, ...f] = line.trim().split(/\s+/);
      if (kind === "P") {
        const pts: Point[] = [];
        for (let i = 0; i < f.length; i += 2) pts.push([Number(f[i]), Number(f[i + 1])]);
        sched = { ...sched, points: pts };
      } else if (kind === "R") {
        sched = { ...sched, wakeRampMin: Number(f[0]), wakeTargetC: Number(f[1]) };
      } else if (kind === "S") {
        const got = setpoint(sched, Number(f[0]), f[1] === "-" ? null : Number(f[1]));
        const ok = f[2] === "off" ? got === null : got !== null && Math.abs(got - Number(f[2])) < 1e-3;
        if (!ok) failures.push(`${line} -> ${got}`);
        checked++;
      } else if (kind === "W") {
        const got = wakeOffset(Number(f[0]), Number(f[1]));
        if (got !== Number(f[2])) failures.push(`${line} -> ${got}`);
        checked++;
      }
    }
    expect(failures).toEqual([]);
    expect(checked).toBeGreaterThanOrEqual(700);
  });

  it("default curve equals opod.schedule.DEFAULT", () => {
    expect(DEFAULT_SCHEDULE.points).toEqual([[0, 24], [30, 21], [120, 20], [300, 23], [420, 25]]);
    expect(DEFAULT_SCHEDULE.wakeRampMin).toBe(30);
    expect(DEFAULT_SCHEDULE.wakeTargetC).toBe(32);
  });
});

describe("config parsing", () => {
  it("reads ESPHome-style durations", () => {
    expect(parseMinutes(30)).toBe(30);
    expect(parseMinutes("30min")).toBe(30);
    expect(parseMinutes("2h")).toBe(120);
    expect(parseMinutes("1h30min")).toBe(90);
    expect(parseMinutes("90s")).toBe(1.5);
    expect(parseMinutes("45")).toBe(45);
    expect(() => parseMinutes("soon")).toThrow();
    expect(() => parseMinutes("30minutes")).toThrow();
  });

  it("builds a schedule from either point form, with defaults", () => {
    const s = scheduleFromConfig([{ at: "0min", temperature: 22 }, [60, 16]], "20min", 35);
    expect(s).toEqual({ points: [[0, 22], [60, 16]], wakeRampMin: 20, wakeTargetC: 35 });
    expect(scheduleFromConfig(undefined, undefined, undefined)).toEqual(DEFAULT_SCHEDULE);
    expect(() => scheduleFromConfig([[60, 20], [30, 21]], undefined, undefined)).toThrow(/sorted/);
  });
});

describe("sampleNight", () => {
  it("runs from bedtime to wake and ends at the wake temperature", () => {
    const pts = sampleNight(DEFAULT_SCHEDULE, 480, 5);
    expect(pts[0]).toEqual([0, 24]);
    expect(pts.at(-1)![0]).toBe(480);
    expect(pts.at(-1)![1]).toBeCloseTo(32, 3);
    expect(pts.every(([, c]) => Number.isFinite(c))).toBe(true);
  });

  it("without a wake time it shows the curve plus an hour", () => {
    const pts = sampleNight(DEFAULT_SCHEDULE, null, 10);
    expect(pts.at(-1)).toEqual([480, 25]);
  });
});
