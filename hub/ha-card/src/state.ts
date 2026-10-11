// Home Assistant states -> what one bed side shows. Pure functions, no DOM.
import { setpoint, wakeOffset, type Schedule } from "./schedule";
import type { CardConfig, HassEntity, HomeAssistant, SideConfig } from "./types";

export type Action = "cooling" | "heating" | "idle" | "off" | "unknown";
/** ok, or why the side can't be trusted: the hub is gone, the hub is up but the control board isn't, or bad config. */
export type Status = "ok" | "hub-offline" | "board-offline" | "missing";

export interface NightPosition {
  /** Minutes since the program was switched on (estimated from the switch's last change). */
  minute: number;
  /** Minutes from bedtime to the wake time, or null without a wake time. */
  wakeMinute: number | null;
  /** Curve setpoint now, or null once past wake. */
  setpoint: number | null;
}

export interface SideView {
  name: string;
  status: Status;
  on: boolean;
  current: number | null;
  target: number | null;
  min: number;
  max: number;
  step: number;
  action: Action;
  program: { on: boolean; available: boolean } | null;
  wake: { minuteOfDay: number | null; available: boolean } | null;
  night: NightPosition | null;
  problem: boolean;
  details: { heatsink: number | null; tec: number | null; flow: number | null };
}

export const ACTION_LABEL: Record<Action, string> = {
  cooling: "Cooling",
  heating: "Heating",
  idle: "Idle",
  off: "Off",
  unknown: "—",
};

const DEAD = new Set(["unavailable", "unknown"]);

export function isDead(e: HassEntity | undefined): boolean {
  return !e || DEAD.has(e.state);
}

/** Numeric state, or null when missing/unavailable/not a number. */
export function numState(e: HassEntity | undefined): number | null {
  if (isDead(e)) return null;
  const v = Number(e!.state);
  return Number.isFinite(v) ? v : null;
}

function numAttr(e: HassEntity, key: string): number | null {
  const v = e.attributes[key];
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

/** "07:00:00" / "07:00" -> 420 (minutes since midnight). */
export function parseTimeOfDay(s: string | undefined): number | null {
  const m = /^(\d{1,2}):(\d{2})(?::\d{2}(?:\.\d+)?)?$/.exec(s ?? "");
  if (!m) return null;
  const h = Number(m[1]);
  const min = Number(m[2]);
  return h < 24 && min < 60 ? h * 60 + min : null;
}

export function formatTimeOfDay(minuteOfDay: number, h12 = false): string {
  const h = Math.floor(minuteOfDay / 60) % 24;
  const m = String(Math.floor(minuteOfDay % 60)).padStart(2, "0");
  if (!h12) return `${String(h).padStart(2, "0")}:${m}`;
  return `${h % 12 || 12}:${m} ${h < 12 ? "AM" : "PM"}`;
}

/** Whole minutes since midnight of `date` in `timeZone` (HA's zone; the hub's clock comes from HA). */
export function minuteOfDay(date: Date, timeZone?: string): number {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const get = (t: string) => Number(parts.find((p) => p.type === t)?.value ?? 0);
  return get("hour") * 60 + get("minute");
}

/**
 * Where the running program is on its curve. The hub stores its own start time; the card only sees when the switch
 * last changed, which also resets on a Home Assistant restart, so this is an estimate. The hub fixes the wake time at
 * start; the card uses the current wake entity.
 */
export function nightPosition(
  sched: Schedule,
  since: Date,
  now: Date,
  wakeMinuteOfDay: number | null,
  timeZone?: string,
): NightPosition {
  const minute = Math.max(0, (now.getTime() - since.getTime()) / 60000);
  const wakeMinute = wakeMinuteOfDay === null ? null : wakeOffset(minuteOfDay(since, timeZone), wakeMinuteOfDay);
  return { minute, wakeMinute, setpoint: setpoint(sched, minute, wakeMinute) };
}

/** Round to the entity's step and clamp to its range (what climate.set_temperature will accept). */
export function clampTarget(v: number, min: number, max: number, step: number): number {
  const r = Math.round(v / step) * step;
  return Math.min(max, Math.max(min, Number(r.toFixed(3))));
}

function toAction(climate: HassEntity): Action {
  if (climate.state === "off") return "off";
  const a = climate.attributes.hvac_action;
  return a === "cooling" || a === "heating" || a === "idle" || a === "off" ? a : "unknown";
}

export function sideView(
  hass: HomeAssistant,
  side: SideConfig,
  index: number,
  card: Pick<CardConfig, "link">,
  sched: Schedule,
  now: Date,
): SideView {
  const s = (id?: string) => (id ? hass.states[id] : undefined);
  const climate = s(side.climate);
  const link = s(card.link);
  const name = side.name ?? (climate?.attributes.friendly_name as string | undefined) ?? `Side ${index + 1}`;

  let status: Status = "ok";
  if (!climate) status = "missing";
  else if (climate.state === "unavailable" || (link && link.state === "unavailable")) status = "hub-offline";
  else if (link && link.state === "off") status = "board-offline";

  const ok = climate && status !== "missing" && status !== "hub-offline";
  const min = (climate && numAttr(climate, "min_temp")) ?? 13;
  const max = (climate && numAttr(climate, "max_temp")) ?? 43;
  const step = (climate && numAttr(climate, "target_temp_step")) ?? 0.5;

  const prog = s(side.program);
  const programOn = prog?.state === "on";
  const wakeEnt = s(side.wake_time);
  const wakeMin = isDead(wakeEnt) ? null : parseTimeOfDay(wakeEnt!.state);

  let night: NightPosition | null = null;
  if (ok && programOn && prog) {
    night = nightPosition(sched, new Date(prog.last_changed), now, wakeMin, hass.config?.time_zone);
  }

  const problemEnt = s(side.problem);
  return {
    name,
    status,
    on: !!ok && climate!.state !== "off",
    current: ok && status === "ok" ? numAttr(climate!, "current_temperature") : null,
    target: ok ? numAttr(climate!, "temperature") : null,
    min,
    max,
    step,
    action: ok ? toAction(climate!) : "unknown",
    program: side.program ? { on: programOn, available: !!ok && !isDead(prog) } : null,
    wake: side.wake_time ? { minuteOfDay: wakeMin, available: !!ok && !isDead(wakeEnt) } : null,
    night,
    // The hub turns "problem" on while the control board link is down too; the offline banner says that already.
    problem: status === "ok" && problemEnt?.state === "on",
    details: {
      heatsink: status === "ok" ? numState(s(side.heatsink)) : null,
      tec: status === "ok" ? numState(s(side.tec_current)) : null,
      flow: status === "ok" ? numState(s(side.flow)) : null,
    },
  };
}

/** Service call that sets a wake time entity (ESPHome `datetime` with `type: time` is a `time` entity in HA). */
export function wakeServiceCall(
  entityId: string,
  minuteOfDay: number,
): { domain: string; service: string; data: Record<string, unknown> } {
  const domain = entityId.split(".")[0];
  const time = `${formatTimeOfDay(minuteOfDay)}:00`;
  if (domain === "input_datetime") return { domain, service: "set_datetime", data: { entity_id: entityId, time } };
  if (domain === "time") return { domain, service: "set_value", data: { entity_id: entityId, time } };
  throw new Error(`wake_time must be a time or input_datetime entity, got ${entityId}`);
}

export function validateConfig(config: unknown): CardConfig {
  const c = config as Partial<CardConfig> | undefined;
  if (!c || !Array.isArray(c.sides) || c.sides.length < 1 || c.sides.length > 2) {
    throw new Error("open-bed-climate-card: `sides` must list 1 or 2 bed sides");
  }
  c.sides.forEach((side, i) => {
    if (!side || typeof side.climate !== "string" || !side.climate.startsWith("climate.")) {
      throw new Error(`open-bed-climate-card: sides[${i}].climate must be a climate entity`);
    }
    if (side.wake_time && !/^(time|input_datetime)\./.test(side.wake_time)) {
      throw new Error(`open-bed-climate-card: sides[${i}].wake_time must be a time or input_datetime entity`);
    }
  });
  return c as CardConfig;
}

/** Entity ids that opod-hub-common.yaml produces (device "Open Bed Climate"). */
export function defaultSides(prefix = "open_bed_climate"): SideConfig[] {
  return (["left", "right"] as const).map((s) => ({
    name: s === "left" ? "Left" : "Right",
    climate: `climate.${prefix}_${s}_side`,
    program: `switch.${prefix}_${s}_night_program`,
    wake_time: `time.${prefix}_${s}_wake_time`,
    problem: `binary_sensor.${prefix}_${s}_problem`,
    clear_faults: `button.${prefix}_${s}_clear_faults`,
    heatsink: `sensor.${prefix}_${s}_heatsink_temperature`,
    tec_current: `sensor.${prefix}_${s}_tec_current`,
    flow: `sensor.${prefix}_${s}_flow`,
  }));
}
