import model from "../data/model.json" with { type: "json" };
import type { KitData } from "./schemas.ts";

export interface ModelKit {
  name: string;
  check: {
    min_water_c: number;
    max_water_c: number;
    tec_input_w_per_zone: number;
    aux_w: number;
    zone_current_limit_a: number;
    problems: string[];
  };
  coldest_by_room: { room_c: number; water_c: number; tec_input_w: number }[];
}

export interface KitView {
  id: string;
  data: KitData;
  model: ModelKit;
  psuMarginOk: boolean;
  auxMarginOk: boolean;
}

export const PSU_MARGIN = 0.8; // = obc.kit.PSU_MARGIN

export const MODEL = model as unknown as {
  limits: { setpoint_min_c: number; setpoint_max_c: number };
  schedule_default: { points: [number, number][]; wake_ramp_min: number; wake_target_c: number };
  kits: Record<string, ModelKit>;
};

// Hand-written "best for" lines (01-content §4.1), keyed by kit id. A new kit without one simply shows none.
export const KIT_BLURB: Record<string, string> = {
  "solo-starter": "For a first build and a single sleeper.",
  "duo-standard": "For couples, with our strongest Tier 0 cooling.",
  "duo-reference": "For experienced builders: reference PCBs and the best biometrics.",
};

export function joinKit(id: string, data: KitData): KitView {
  const m = MODEL.kits[id];
  if (!m) throw new Error(`model.json has no kit "${id}". Run: npm run data`);
  return {
    id,
    data,
    model: m,
    psuMarginOk: m.check.tec_input_w_per_zone <= data.power.tec_psu_w_per_zone * PSU_MARGIN,
    auxMarginOk: m.check.aux_w <= data.power.aux_psu_w * PSU_MARGIN,
  };
}

/** Order: zones, then tier, then name. Solo Starter → Duo Standard → Duo Reference. */
export const sortKits = (a: KitView, b: KitView) =>
  a.data.kit.zones - b.data.kit.zones || a.data.kit.tier - b.data.kit.tier || a.data.kit.name.localeCompare(b.data.kit.name);

export function psuSummary(k: KitData): string {
  const zones = k.kit.zones;
  if (k.kit.tier === 1) return `24 V ${k.power.tec_psu_w_per_zone * zones} W in a closed power module + aux ${k.power.aux_psu_w} W`;
  return `${zones > 1 ? `${zones}× ` : ""}24 V ${k.power.tec_psu_w_per_zone} W + 12 V ${k.power.aux_psu_w} W, plug-in`;
}
