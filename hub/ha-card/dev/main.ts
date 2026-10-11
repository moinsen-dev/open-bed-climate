// Dev harness: renders the card against several mocked Home Assistant states. `npm run dev`, then open /dev/.
// Query: ?theme=dark, ?only=<scenario id> (one card, for screenshots).
import "../src/index";
import type { OpenBedClimateCard } from "../src/card";
import { defaultSides } from "../src/state";
import type { CardConfig, HassEntity, HomeAssistant } from "../src/types";

// Minimal stand-in for HA's <ha-card>.
customElements.define(
  "ha-card",
  class extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" }).innerHTML = `<style>:host{display:block;background:var(--ha-card-background,var(--card-background-color));
        border-radius:var(--ha-card-border-radius,12px);border:1px solid var(--ha-card-border-color,var(--divider-color));
        color:var(--primary-text-color)}</style><slot></slot>`;
    }
  },
);

const params = new URLSearchParams(location.search);
const dark = params.get("theme") === "dark";
document.documentElement.dataset.theme = dark ? "dark" : "light";

const NOW = new Date();
NOW.setHours(3, 40, 0, 0);
const minutesAgo = (m: number) => new Date(NOW.getTime() - m * 60000).toISOString();
const [L, R] = defaultSides();
const LINK = "binary_sensor.open_bed_climate_control_board_link";
const PRIME = "button.open_bed_climate_prime_water_loop";

type Side = {
  mode?: "heat_cool" | "off" | "unavailable";
  action?: string;
  water?: number | null;
  target?: number;
  program?: "on" | "off";
  since?: number;
  wake?: string;
  problem?: boolean;
  heatsink?: number;
  tec?: number;
  flow?: number;
};

function sideStates(s: typeof L, v: Side): HassEntity[] {
  const e = (id: string, state: string, attributes: Record<string, unknown> = {}, ago = 30): HassEntity => ({
    entity_id: id,
    state,
    attributes,
    last_changed: minutesAgo(ago),
    last_updated: minutesAgo(ago),
  });
  const dead = v.mode === "unavailable";
  const st = (x: string) => (dead ? "unavailable" : x);
  return [
    e(s.climate, v.mode ?? "heat_cool", {
      hvac_modes: ["off", "heat_cool"],
      min_temp: 13,
      max_temp: 43,
      target_temp_step: 0.5,
      current_temperature: v.water ?? null,
      temperature: v.target ?? 24,
      hvac_action: v.mode === "off" ? "off" : (v.action ?? "idle"),
      friendly_name: "Open Bed Climate Left side",
    }),
    e(s.program!, st(v.program ?? "off"), {}, v.since ?? 600),
    e(s.wake_time!, st(v.wake ?? "07:00:00")),
    e(s.problem!, st(v.problem ? "on" : "off")),
    e(s.clear_faults!, st("unknown")),
    e(s.heatsink!, st(v.heatsink != null ? String(v.heatsink) : "unknown")),
    e(s.tec_current!, st(v.tec != null ? String(v.tec) : "unknown")),
    e(s.flow!, st(v.flow != null ? String(v.flow) : "unknown")),
  ];
}

const log = document.getElementById("log")!;
function hassOf(entities: HassEntity[]): HomeAssistant {
  return {
    states: Object.fromEntries(entities.map((x) => [x.entity_id, x])),
    callService: async (domain, service, data) => {
      log.textContent = `${new Date().toLocaleTimeString()}  ${domain}.${service} ${JSON.stringify(data)}\n` + log.textContent;
    },
    themes: { darkMode: dark },
    config: { time_zone: Intl.DateTimeFormat().resolvedOptions().timeZone },
    locale: { language: "en", time_format: "24" },
  };
}

const misc = (link: string, prime = "unknown") => [
  { entity_id: LINK, state: link, attributes: {}, last_changed: minutesAgo(5), last_updated: minutesAgo(5) },
  { entity_id: PRIME, state: prime, attributes: {}, last_changed: minutesAgo(5), last_updated: minutesAgo(5) },
];

const base: Omit<CardConfig, "type"> = { sides: [L, R], link: LINK, prime: PRIME };
const scenarios: { id: string; caption: string; config?: Partial<CardConfig>; entities: HassEntity[] }[] = [
  {
    id: "night",
    caption: "Program running on the left (cooling), right heating",
    entities: [
      ...sideStates(L, { action: "cooling", water: 20.6, target: 20.5, program: "on", since: 280, heatsink: 36.8, tec: 3.9, flow: 1.18 }),
      ...sideStates(R, { action: "heating", water: 31.2, target: 33, heatsink: 22.4, tec: 2.6, flow: 1.21, wake: "06:30:00" }),
      ...misc("on"),
    ],
  },
  {
    id: "cool",
    caption: "Deep cooling, both sides",
    entities: [
      ...sideStates(L, { action: "cooling", water: 15.2, target: 14, heatsink: 41.5, tec: 4.9, flow: 1.15 }),
      ...sideStates(R, { action: "idle", water: 19.9, target: 20, program: "on", since: 60, heatsink: 30.1, tec: 1.2, flow: 1.19 }),
      ...misc("on"),
    ],
  },
  {
    id: "fault",
    caption: "Fault on the left, right off",
    entities: [
      ...sideStates(L, { mode: "off", water: 24.1, target: 21, problem: true, heatsink: 58.3, tec: 0, flow: 0 }),
      ...sideStates(R, { mode: "off", water: 23.8, target: 22, heatsink: 24, tec: 0, flow: 1.1 }),
      ...misc("on"),
    ],
  },
  {
    id: "board",
    caption: "Hub up, control board not talking",
    entities: [...sideStates(L, { water: null, target: 20 }), ...sideStates(R, { water: null, target: 30, problem: true }), ...misc("off")],
  },
  {
    id: "offline",
    caption: "Hub offline",
    entities: [...sideStates(L, { mode: "unavailable" }), ...sideStates(R, { mode: "unavailable" }), ...misc("unavailable", "unavailable")],
  },
  {
    id: "solo",
    caption: "Solo kit: one side, curve without heatsink row",
    config: {
      title: "Guest bed",
      sides: [{ ...L, name: "Bed", heatsink: undefined, tec_current: undefined, flow: undefined }],
      prime: undefined,
      points: [{ at: "0min", temperature: 22 }, { at: "60min", temperature: 18 }, { at: "4h", temperature: 19.5 }],
      wake_ramp_min: 40,
      wake_temperature: 30,
    },
    entities: [...sideStates(L, { action: "cooling", water: 18.9, target: 18.5, program: "on", since: 150 }), ...misc("on")],
  },
];

const grid = document.getElementById("grid")!;
const only = params.get("only");
if (only) document.querySelector("h1")!.hidden = true;
for (const s of scenarios.filter((x) => !only || x.id === only)) {
  const fig = document.createElement("figure");
  if (!only) fig.innerHTML = `<figcaption>${s.caption}</figcaption>`;
  const card = document.createElement("open-bed-climate-card") as OpenBedClimateCard;
  card.setConfig({ type: "custom:open-bed-climate-card", ...base, ...s.config } as CardConfig);
  card.now = NOW;
  card.hass = hassOf(s.entities);
  fig.append(card);
  grid.append(fig);
}
