import { describe, expect, it } from "vitest";
import { DEFAULT_SCHEDULE } from "../src/schedule";
import {
  clampTarget,
  defaultSides,
  formatTimeOfDay,
  minuteOfDay,
  nightPosition,
  parseTimeOfDay,
  sideView,
  validateConfig,
  wakeServiceCall,
} from "../src/state";
import type { HassEntity, HomeAssistant } from "../src/types";

const NOW = new Date("2026-10-11T02:00:00Z");
const ent = (entity_id: string, state: string, attributes: Record<string, unknown> = {}, last_changed = NOW.toISOString()): HassEntity => ({
  entity_id,
  state,
  attributes,
  last_changed,
  last_updated: last_changed,
});
const hassOf = (...es: HassEntity[]): HomeAssistant => ({
  states: Object.fromEntries(es.map((e) => [e.entity_id, e])),
  callService: async () => undefined,
  config: { time_zone: "UTC" },
});
const [LEFT] = defaultSides();
const climate = (state: string, attrs: Record<string, unknown> = {}) =>
  ent(LEFT.climate, state, { min_temp: 13, max_temp: 43, target_temp_step: 0.5, current_temperature: 21.4, temperature: 20, hvac_action: "cooling", ...attrs });
const view = (hass: HomeAssistant, link?: string) => sideView(hass, LEFT, 0, { link }, DEFAULT_SCHEDULE, NOW);
const LINK = "binary_sensor.open_bed_climate_control_board_link";

describe("sideView", () => {
  it("maps a cooling side", () => {
    const v = view(hassOf(climate("heat_cool"), ent(LEFT.heatsink!, "38.2"), ent(LEFT.tec_current!, "4.1"), ent(LEFT.flow!, "1.20")));
    expect(v).toMatchObject({ name: "Left", status: "ok", on: true, current: 21.4, target: 20, action: "cooling", problem: false });
    expect(v.details).toEqual({ heatsink: 38.2, tec: 4.1, flow: 1.2 });
  });

  it("off mode reads as off whatever hvac_action says", () => {
    expect(view(hassOf(climate("off", { hvac_action: "idle" }))).action).toBe("off");
    expect(view(hassOf(climate("off"))).on).toBe(false);
  });

  it("unavailable climate = hub offline, nothing to show or control", () => {
    const v = view(hassOf(ent(LEFT.climate, "unavailable")));
    expect(v).toMatchObject({ status: "hub-offline", on: false, current: null, target: null, action: "unknown" });
  });

  it("link off = control board offline: no readings, no problem banner on top", () => {
    const v = view(hassOf(climate("heat_cool", { current_temperature: null }), ent(LEFT.problem!, "on"), ent(LINK, "off")), LINK);
    expect(v).toMatchObject({ status: "board-offline", current: null, target: 20, problem: false });
  });

  it("missing climate entity", () => {
    expect(view(hassOf()).status).toBe("missing");
  });

  it("problem on shows the fault", () => {
    expect(view(hassOf(climate("heat_cool"), ent(LEFT.problem!, "on"), ent(LINK, "on")), LINK).problem).toBe(true);
  });

  it("uses the entity's range and step", () => {
    expect(view(hassOf(climate("heat_cool", { min_temp: 15, max_temp: 40, target_temp_step: 1 })))).toMatchObject({ min: 15, max: 40, step: 1 });
    expect(view(hassOf(climate("heat_cool", { min_temp: undefined })))).toMatchObject({ min: 13 });
  });

  it("estimates the night position from the program switch", () => {
    const since = new Date(NOW.getTime() - 90 * 60000).toISOString(); // switched on at 00:30 UTC
    const v = view(hassOf(climate("heat_cool"), ent(LEFT.program!, "on", {}, since), ent(LEFT.wake_time!, "07:00:00")));
    expect(v.program).toEqual({ on: true, available: true });
    expect(v.wake).toEqual({ minuteOfDay: 420, available: true });
    expect(v.night!.minute).toBeCloseTo(90);
    expect(v.night!.wakeMinute).toBe(390);
    expect(v.night!.setpoint).toBeCloseTo(21 - 60 / 90, 3); // between the 30 and 120 min points
  });

  it("no night position while the program is off", () => {
    expect(view(hassOf(climate("heat_cool"), ent(LEFT.program!, "off"))).night).toBeNull();
  });
});

describe("helpers", () => {
  it("clampTarget rounds to the step and clamps", () => {
    expect(clampTarget(20.26, 13, 43, 0.5)).toBe(20.5);
    expect(clampTarget(12, 13, 43, 0.5)).toBe(13);
    expect(clampTarget(43.5, 13, 43, 0.5)).toBe(43);
    expect(clampTarget(20.1 + 0.2, 13, 43, 0.1)).toBe(20.3);
  });

  it("time of day parsing and formatting", () => {
    expect(parseTimeOfDay("07:00:00")).toBe(420);
    expect(parseTimeOfDay("6:45")).toBe(405);
    expect(parseTimeOfDay("25:00")).toBeNull();
    expect(parseTimeOfDay("unknown")).toBeNull();
    expect(formatTimeOfDay(420)).toBe("07:00");
    expect(formatTimeOfDay(1380, true)).toBe("11:00 PM");
    expect(formatTimeOfDay(5, true)).toBe("12:05 AM");
  });

  it("minuteOfDay honours the HA time zone", () => {
    expect(minuteOfDay(new Date("2026-10-11T22:30:00Z"), "UTC")).toBe(1350);
    expect(minuteOfDay(new Date("2026-10-11T22:30:00Z"), "Europe/Berlin")).toBe(30); // CEST, +2
  });

  it("nightPosition: bedtime 23:00, wake 07:00 -> 480 min night", () => {
    const since = new Date("2026-10-11T23:00:00Z");
    const p = nightPosition(DEFAULT_SCHEDULE, since, new Date("2026-10-12T06:45:00Z"), 420, "UTC");
    expect(p.wakeMinute).toBe(480);
    expect(p.minute).toBe(465);
    expect(p.setpoint).toBeCloseTo(25 + (32 - 25) * 0.5, 3); // halfway up the wake ramp
    expect(nightPosition(DEFAULT_SCHEDULE, since, new Date("2026-10-12T07:01:00Z"), 420, "UTC").setpoint).toBeNull();
  });

  it("wake service call per domain", () => {
    expect(wakeServiceCall("time.open_bed_climate_left_wake_time", 405)).toEqual({
      domain: "time",
      service: "set_value",
      data: { entity_id: "time.open_bed_climate_left_wake_time", time: "06:45:00" },
    });
    expect(wakeServiceCall("input_datetime.wake", 420).service).toBe("set_datetime");
    expect(() => wakeServiceCall("sensor.x", 420)).toThrow();
  });

  it("validateConfig", () => {
    expect(() => validateConfig({ type: "x" })).toThrow(/sides/);
    expect(() => validateConfig({ sides: [{ climate: "switch.x" }] })).toThrow(/climate/);
    expect(() => validateConfig({ sides: [{ climate: "climate.a" }, { climate: "climate.b" }, { climate: "climate.c" }] })).toThrow();
    expect(() => validateConfig({ sides: [{ climate: "climate.a", wake_time: "sensor.t" }] })).toThrow(/wake_time/);
    expect(validateConfig({ sides: defaultSides() }).sides).toHaveLength(2);
  });

  it("default entity ids follow ESPHome naming for obc-hub-common.yaml", () => {
    expect(defaultSides()[1]).toEqual({
      name: "Right",
      climate: "climate.open_bed_climate_right_side",
      program: "switch.open_bed_climate_right_night_program",
      wake_time: "time.open_bed_climate_right_wake_time",
      problem: "binary_sensor.open_bed_climate_right_problem",
      clear_faults: "button.open_bed_climate_right_clear_faults",
      heatsink: "sensor.open_bed_climate_right_heatsink_temperature",
      tec_current: "sensor.open_bed_climate_right_tec_current",
      flow: "sensor.open_bed_climate_right_flow",
    });
  });
});
