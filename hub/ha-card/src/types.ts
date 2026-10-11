// The parts of Home Assistant's frontend API this card uses (kept local: no runtime dependency on HA packages).

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed: string;
  last_updated: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntity | undefined>;
  callService(domain: string, service: string, data?: Record<string, unknown>): Promise<unknown>;
  themes?: { darkMode?: boolean };
  config?: { time_zone?: string };
  locale?: { language?: string; time_format?: string };
  language?: string;
}

export interface SideConfig {
  name?: string;
  climate: string;
  program?: string;
  wake_time?: string;
  problem?: string;
  clear_faults?: string;
  heatsink?: string;
  tec_current?: string;
  flow?: string;
}

export interface CardConfig {
  type: string;
  title?: string;
  sides: SideConfig[];
  link?: string;
  prime?: string;
  points?: import("./schedule").PointInput[];
  wake_ramp_min?: number | string;
  wake_temperature?: number;
}
