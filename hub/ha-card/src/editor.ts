import { html, LitElement, nothing } from "lit";
import type { CardConfig, HomeAssistant, SideConfig } from "./types";

// Visual editor: Home Assistant's own <ha-form> with entity pickers, one section per side. The nested `sides` list is
// flattened to s0_climate, s1_climate, ... for the form and rebuilt on change. `points` stays YAML-only.
const SIDE_FIELDS: { key: keyof SideConfig; label: string; selector: Record<string, unknown> }[] = [
  { key: "name", label: "Name", selector: { text: {} } },
  { key: "climate", label: "Climate (required)", selector: { entity: { domain: "climate" } } },
  { key: "program", label: "Night program switch", selector: { entity: { domain: "switch" } } },
  { key: "wake_time", label: "Wake time", selector: { entity: { domain: ["time", "input_datetime"] } } },
  { key: "problem", label: "Problem", selector: { entity: { domain: "binary_sensor" } } },
  { key: "clear_faults", label: "Clear faults button", selector: { entity: { domain: "button" } } },
  { key: "heatsink", label: "Heatsink temperature", selector: { entity: { domain: "sensor" } } },
  { key: "tec_current", label: "TEC current", selector: { entity: { domain: "sensor" } } },
  { key: "flow", label: "Flow", selector: { entity: { domain: "sensor" } } },
];

const CARD_FIELDS = [
  { name: "title", label: "Title", selector: { text: {} } },
  { name: "link", label: "Control board link", selector: { entity: { domain: "binary_sensor" } } },
  { name: "prime", label: "Prime button", selector: { entity: { domain: "button" } } },
  { name: "wake_ramp_min", label: "Wake ramp (min)", selector: { number: { min: 0, max: 180, step: 5, mode: "box" } } },
  { name: "wake_temperature", label: "Wake temperature (°C)", selector: { number: { min: 13, max: 43, step: 0.5, mode: "box" } } },
];

export class OpenBedClimateCardEditor extends LitElement {
  static override properties = { hass: { attribute: false }, _config: { state: true } };
  declare hass?: HomeAssistant;
  declare _config?: CardConfig;

  setConfig(config: CardConfig): void {
    this._config = config;
  }

  private _schema() {
    const sides = [0, 1].map((i) => ({
      type: "expandable",
      flatten: true,
      expanded: i === 0,
      title: i === 0 ? "Side 1" : "Side 2 (optional)",
      schema: SIDE_FIELDS.map((f) => ({ name: `s${i}_${f.key}`, selector: f.selector, required: i === 0 && f.key === "climate" })),
    }));
    return [...sides, { type: "expandable", flatten: true, title: "Card", schema: CARD_FIELDS }];
  }

  private _data(): Record<string, unknown> {
    const c = this._config!;
    const d: Record<string, unknown> = {};
    for (const f of CARD_FIELDS) d[f.name] = c[f.name as keyof CardConfig];
    c.sides?.forEach((s, i) => SIDE_FIELDS.forEach((f) => (d[`s${i}_${f.key}`] = s[f.key])));
    return d;
  }

  private _changed(ev: CustomEvent<{ value: Record<string, unknown> }>): void {
    const v = ev.detail.value;
    const config: Record<string, unknown> = { ...this._config };
    for (const f of CARD_FIELDS) {
      if (v[f.name] === undefined || v[f.name] === "") delete config[f.name];
      else config[f.name] = v[f.name];
    }
    const sides: SideConfig[] = [];
    for (const i of [0, 1]) {
      const s: Record<string, unknown> = {};
      for (const f of SIDE_FIELDS) if (v[`s${i}_${f.key}`]) s[f.key] = v[`s${i}_${f.key}`];
      if (s.climate || i === 0) sides.push(s as unknown as SideConfig);
    }
    config.sides = sides;
    this._config = config as unknown as CardConfig;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }

  override render() {
    if (!this._config) return nothing;
    if (!customElements.get("ha-form")) return html`<p>Edit this card in YAML (see the card's README).</p>`;
    const labels = new Map<string, string>([
      ...CARD_FIELDS.map((f) => [f.name, f.label] as [string, string]),
      ...[0, 1].flatMap((i) => SIDE_FIELDS.map((f) => [`s${i}_${f.key}`, f.label] as [string, string])),
    ]);
    return html`<ha-form
      .hass=${this.hass}
      .data=${this._data()}
      .schema=${this._schema()}
      .computeLabel=${(s: { name: string }) => labels.get(s.name) ?? s.name}
      @value-changed=${this._changed}
    ></ha-form>`;
  }
}
