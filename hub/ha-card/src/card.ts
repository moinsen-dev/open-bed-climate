import { html, LitElement, nothing, svg, type PropertyValues, type TemplateResult } from "lit";
import { sideColors, tempColor, INK_STOPS, NIGHT_STOPS } from "./color";
import { sampleNight, scheduleFromConfig, type Schedule } from "./schedule";
import {
  ACTION_LABEL,
  clampTarget,
  defaultSides,
  formatTimeOfDay,
  minuteOfDay,
  sideView,
  validateConfig,
  wakeServiceCall,
  type SideView,
} from "./state";
import { styles } from "./styles";
import type { CardConfig, HomeAssistant } from "./types";

// Material Design Icons paths (Apache-2.0, pictogrammers.com).
const ICON = {
  power:
    "M16.56,5.44L15.11,6.89C16.84,7.94 18,9.83 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12C6,9.83 7.16,7.94 8.88,6.88L7.44,5.44C5.36,6.88 4,9.28 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12C20,9.28 18.64,6.88 16.56,5.44M13,3H11V13H13",
  minus: "M19,13H5V11H19V13Z",
  plus: "M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",
  clock:
    "M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z",
  alert:
    "M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z",
  offline:
    "M19.35,10.03C18.67,6.59 15.64,4 12,4C10.88,4 9.82,4.25 8.87,4.68L10.39,6.2C10.9,6.07 11.44,6 12,6A5.5,5.5 0 0,1 17.5,11.5V12H19A3,3 0 0,1 22,15C22,16.13 21.36,17.11 20.43,17.62L21.88,19.07C23.16,18.16 24,16.68 24,15C24,12.36 21.95,10.22 19.35,10.03M3,5.27L5.75,8C2.56,8.15 0,10.77 0,14A6,6 0 0,0 6,20H17.73L19.73,22L21,20.73L4.27,4L3,5.27M7.73,10L15.73,18H6A4,4 0 0,1 2,14A4,4 0 0,1 6,10H7.73Z",
};
const icon = (d: string) => html`<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d=${d}></path></svg>`;

const fmt = (v: number | null, digits: number) => (v === null ? "—" : v.toFixed(digits));
const SEND_DELAY_MS = 700;
const PENDING_TIMEOUT_MS = 6000;

interface Pending {
  value: number;
  timer?: number;
  sentAt?: number;
}

export class OpenBedClimateCard extends LitElement {
  static override styles = styles;
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
    _pending: { state: true },
    _confirm: { state: true },
    _editingWake: { state: true },
  };

  declare hass?: HomeAssistant;
  declare _config?: CardConfig;
  declare _pending: Record<number, Pending>;
  declare _confirm: number | null;
  declare _editingWake: number | null;
  private _schedule: Schedule = scheduleFromConfig(undefined, undefined, undefined);
  private _tick?: number;
  /** Fixed clock for the dev harness and screenshots. */
  now?: Date;

  constructor() {
    super();
    this._pending = {};
    this._confirm = null;
    this._editingWake = null;
  }

  // ---- Lovelace card API -------------------------------------------------------------------------------------

  setConfig(config: CardConfig): void {
    const c = validateConfig(config);
    this._schedule = scheduleFromConfig(c.points, c.wake_ramp_min, c.wake_temperature);
    this._config = c;
  }

  static getConfigElement(): HTMLElement {
    return document.createElement("open-bed-climate-card-editor");
  }

  static getStubConfig(hass?: HomeAssistant): Omit<CardConfig, "type"> {
    const sides = defaultSides();
    if (hass && !hass.states[sides[0].climate]) {
      const climate = Object.keys(hass.states).find((id) => id.startsWith("climate."));
      if (climate) return { sides: [{ climate }] };
    }
    return {
      sides,
      link: "binary_sensor.open_bed_climate_control_board_link",
      prime: "button.open_bed_climate_prime_water_loop",
    };
  }

  getCardSize(): number {
    return 8;
  }

  getGridOptions() {
    const one = this._config?.sides.length === 1;
    return { columns: one ? 6 : 12, min_columns: 6, rows: "auto" };
  }

  // ---- lifecycle ---------------------------------------------------------------------------------------------

  override connectedCallback(): void {
    super.connectedCallback();
    // The night marker moves with the clock even when no state changes.
    this._tick = window.setInterval(() => this.requestUpdate(), 60_000);
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    window.clearInterval(this._tick);
    for (const p of Object.values(this._pending)) window.clearTimeout(p.timer);
  }

  override shouldUpdate(changed: PropertyValues): boolean {
    if (!changed.has("hass") || changed.size > 1 || !this._config) return true;
    const old = changed.get("hass") as HomeAssistant | undefined;
    if (!old || old.themes?.darkMode !== this.hass?.themes?.darkMode) return true;
    return this._entityIds().some((id) => old.states[id] !== this.hass!.states[id]);
  }

  override willUpdate(changed: PropertyValues): void {
    // Drop a pending target once Home Assistant reports it (or after a timeout, e.g. the hub rejected it).
    if (!changed.has("hass") || !this.hass || !this._config) return;
    let next: Record<number, Pending> | null = null;
    this._config.sides.forEach((side, i) => {
      const p = this._pending[i];
      if (!p?.sentAt) return;
      const t = Number(this.hass!.states[side.climate]?.attributes.temperature);
      if (Math.abs(t - p.value) < 1e-6) {
        window.clearTimeout(p.timer);
        next ??= { ...this._pending };
        delete next[i];
      }
    });
    if (next) this._pending = next;
  }

  private _entityIds(): string[] {
    const c = this._config!;
    const ids = [c.link, c.prime];
    for (const s of c.sides) ids.push(s.climate, s.program, s.wake_time, s.problem, s.clear_faults, s.heatsink, s.tec_current, s.flow);
    return ids.filter((x): x is string => !!x);
  }

  // ---- actions -----------------------------------------------------------------------------------------------

  private _call(domain: string, service: string, data: Record<string, unknown>): void {
    this.hass?.callService(domain, service, data).catch((err: unknown) => {
      console.error(`open-bed-climate-card: ${domain}.${service} failed`, err);
    });
  }

  private _step(i: number, v: SideView, dir: 1 | -1): void {
    const from = this._pending[i]?.value ?? v.target ?? (v.current !== null ? clampTarget(v.current, v.min, v.max, v.step) : 24);
    const value = clampTarget(from + dir * v.step, v.min, v.max, v.step);
    window.clearTimeout(this._pending[i]?.timer);
    const entity_id = this._config!.sides[i].climate;
    const timer = window.setTimeout(() => {
      // Give up on the shown value if Home Assistant never reports it (e.g. the hub rejected it).
      const expire = window.setTimeout(() => {
        if (this._pending[i]?.timer !== expire) return;
        const { [i]: _drop, ...rest } = this._pending;
        this._pending = rest;
      }, PENDING_TIMEOUT_MS);
      this._pending = { ...this._pending, [i]: { value, sentAt: Date.now(), timer: expire } };
      this._call("climate", "set_temperature", { entity_id, temperature: value });
    }, SEND_DELAY_MS);
    this._pending = { ...this._pending, [i]: { value, timer } };
  }

  private _power(i: number, v: SideView): void {
    this._call("climate", "set_hvac_mode", { entity_id: this._config!.sides[i].climate, hvac_mode: v.on ? "off" : "heat_cool" });
  }

  private _program(i: number, on: boolean): void {
    this._call("switch", on ? "turn_off" : "turn_on", { entity_id: this._config!.sides[i].program });
  }

  /** Commit an edited wake time (on Enter or leaving the field; typing alone sends nothing). */
  private _setWake(i: number, value: string): void {
    if (this._editingWake !== i) return;
    const [h, m] = value.split(":").map(Number);
    const current = this.hass?.states[this._config!.sides[i].wake_time!]?.state.slice(0, 5);
    if (Number.isFinite(h) && Number.isFinite(m) && value.slice(0, 5) !== current) {
      const c = wakeServiceCall(this._config!.sides[i].wake_time!, h * 60 + m);
      this._call(c.domain, c.service, c.data);
    }
    this._editingWake = null;
  }

  private _press(entity_id: string): void {
    this._call("button", "press", { entity_id });
  }

  // ---- render ------------------------------------------------------------------------------------------------

  private get _dark(): boolean {
    return !!this.hass?.themes?.darkMode;
  }

  private get _h12(): boolean {
    const f = this.hass?.locale?.time_format;
    if (f === "12") return true;
    if (f === "24") return false;
    const lang = this.hass?.locale?.language ?? this.hass?.language;
    try {
      return !!new Intl.DateTimeFormat(lang, { hour: "numeric" }).resolvedOptions().hour12;
    } catch {
      return false;
    }
  }

  override render(): TemplateResult | typeof nothing {
    if (!this._config || !this.hass) return nothing;
    const c = this._config;
    const now = this.now ?? new Date();
    const views = c.sides.map((s, i) => sideView(this.hass!, s, i, c, this._schedule, now));
    const link = c.link ? this.hass.states[c.link] : undefined;
    const hubOff = views.every((v) => v.status === "hub-offline" || v.status === "missing");
    const boardOff = !hubOff && link?.state === "off";
    const prime = c.prime ? this.hass.states[c.prime] : undefined;
    const canPrime = !!prime && prime.state !== "unavailable" && !hubOff && !boardOff;

    return html`
      <ha-card style=${`--obc-scheme:${this._dark ? "dark" : "light"}`}>
        <header>
          <h2>${c.title ?? "Bed climate"}</h2>
          ${hubOff
            ? html`<span class="pill bad" role="status">${icon(ICON.offline)} Hub offline</span>`
            : boardOff
              ? html`<span class="pill bad" role="status"><span class="dot"></span> Control board offline</span>`
              : nothing}
          ${canPrime
            ? html`<button class="pill action" @click=${() => this._press(c.prime!)} title="Run the pump-only priming cycle">
                Prime loop
              </button>`
            : nothing}
        </header>
        <div class="bed ${c.sides.length === 1 ? "single" : ""}">
          <div class="headboard" aria-hidden="true"></div>
          <div class="mattress" style=${`--sides:${c.sides.length};--rows:6`}>${views.map((v, i) => this._side(v, i))}</div>
        </div>
      </ha-card>
    `;
  }

  private _side(v: SideView, i: number): TemplateResult {
    const side = this._config!.sides[i];
    const usable = v.status === "ok" || v.status === "board-offline";
    // Tint by the water temperature only: without a reading (hub or control board offline) the side is grey.
    const colors = sideColors(v.current, this._dark);
    const style = colors ? `--fill:${colors.fill};--ink:${colors.ink}` : "";
    const cls = ["side", v.status === "ok" ? "" : "offline", v.on ? "" : "off"].join(" ");
    const pending = this._pending[i]?.value;
    const target = pending ?? v.target;
    const running = v.on && (v.action === "cooling" || v.action === "heating");

    return html`
      <section class=${cls} style=${style} aria-label=${`${v.name} side`}>
        <div class="pillow"><span class="caps">${v.name}</span></div>

        ${v.problem
          ? this._problem(v, i)
          : !usable
            ? html`<div class="offline-note" role="status">
                ${icon(ICON.offline)} ${v.status === "missing" ? "Entity not found" : "Hub offline"}
              </div>`
            : html`<div class="row">
                <span class="state ${running ? "running" : ""}">
                  <span class="dot" aria-hidden="true"></span>
                  <span class="caps">${v.status === "board-offline" ? "No board" : ACTION_LABEL[v.action]}</span>
                </span>
                <button
                  class="icon-btn power"
                  aria-pressed=${v.on ? "true" : "false"}
                  aria-label=${`${v.name}: turn ${v.on ? "off" : "on"}`}
                  title=${v.on ? "Turn off" : "Turn on"}
                  @click=${() => this._power(i, v)}
                >
                  ${icon(ICON.power)}
                </button>
              </div>`}

        <div class="readout">
          <span class="big num ${v.current === null ? "none" : ""}">${fmt(v.current, 1)}</span>${v.current === null ? nothing : html`<span class="unit">°C</span>`}
          <span class="caps">Water</span>
        </div>

        <div class="stepper">
          <button
            class="icon-btn"
            aria-label=${`${v.name}: lower target`}
            ?disabled=${!usable || (target !== null && target <= v.min)}
            @click=${() => this._step(i, v, -1)}
          >
            ${icon(ICON.minus)}
          </button>
          <div class="value" aria-live="polite">
            <strong class="num ${pending !== undefined ? "pending" : ""}">${fmt(target, 1)}</strong><span class="unit"> °C</span>
            <span class="caps">${v.on || pending !== undefined ? "Target" : "Target · off"}</span>
          </div>
          <button
            class="icon-btn"
            aria-label=${`${v.name}: raise target`}
            ?disabled=${!usable || (target !== null && target >= v.max)}
            @click=${() => this._step(i, v, 1)}
          >
            ${icon(ICON.plus)}
          </button>
        </div>

        ${side.program || side.wake_time ? this._night(v, i, usable) : nothing}
        ${side.heatsink || side.tec_current || side.flow
          ? html`<div class="details">
              ${side.heatsink ? html`<div><strong class="num">${fmt(v.details.heatsink, 1)}°</strong><span class="caps" title="Heatsink">Sink</span></div>` : nothing}
              ${side.tec_current ? html`<div><strong class="num">${fmt(v.details.tec, 1)} A</strong><span class="caps">TEC</span></div>` : nothing}
              ${side.flow ? html`<div><strong class="num">${fmt(v.details.flow, 2)}</strong><span class="caps">L/min</span></div>` : nothing}
            </div>`
          : nothing}
      </section>
    `;
  }

  private _problem(v: SideView, i: number): TemplateResult {
    const btn = this._config!.sides[i].clear_faults;
    const confirming = this._confirm === i;
    return html`
      <div class="banner" role="alert">
        <span class="title">${icon(ICON.alert)} ${confirming ? "Clear faults?" : "Problem"}</span>
        <span>
          ${confirming
            ? "Only after you have found and fixed the cause (leak, over-temperature, sensor). See the hub log."
            : `${v.name} stopped on a fault.`}
        </span>
        ${btn
          ? html`<div class="actions">
              ${confirming
                ? html`<button
                      class="text-btn danger"
                      @click=${() => {
                        this._press(btn);
                        this._confirm = null;
                      }}
                    >
                      Clear
                    </button>
                    <button class="text-btn" @click=${() => (this._confirm = null)}>Cancel</button>`
                : html`<button class="text-btn" @click=${() => (this._confirm = i)}>Clear faults…</button>`}
            </div>`
          : nothing}
      </div>
    `;
  }

  private _night(v: SideView, i: number, usable: boolean): TemplateResult {
    const side = this._config!.sides[i];
    const on = !!v.program?.on;
    const wakeText = v.wake?.minuteOfDay != null ? formatTimeOfDay(v.wake.minuteOfDay, this._h12) : "--:--";
    const editing = this._editingWake === i;

    const programToggle = side.program
      ? html`<button
          class="toggle"
          role="switch"
          aria-checked=${on ? "true" : "false"}
          aria-label=${`${v.name} night program`}
          ?disabled=${!usable || !v.program!.available}
          @click=${() => this._program(i, on)}
        >
          <span class="track" aria-hidden="true"></span>Night
        </button>`
      : html`<span class="caps">Wake</span>`;

    const wake = side.wake_time
      ? editing
        ? html`<span class="wake-edit">
            <label class="sr-only" for=${`wake-${i}`}>${v.name} wake time</label>
            <input
              id=${`wake-${i}`}
              type="time"
              .value=${v.wake?.minuteOfDay != null ? formatTimeOfDay(v.wake.minuteOfDay) : ""}
              .defaultValue=${v.wake?.minuteOfDay != null ? formatTimeOfDay(v.wake.minuteOfDay) : ""}
              @keydown=${(e: KeyboardEvent) => {
                const input = e.target as HTMLInputElement;
                if (e.key === "Escape") {
                  input.value = input.defaultValue;
                  this._editingWake = null;
                }
                if (e.key === "Enter") input.blur();
              }}
              @blur=${(e: FocusEvent) => this._setWake(i, (e.target as HTMLInputElement).value)}
            />
          </span>`
        : html`<button
            class="wake num"
            aria-label=${`${v.name} wake time ${wakeText}, change`}
            ?disabled=${!usable || !v.wake!.available}
            @click=${async () => {
              this._editingWake = i;
              await this.updateComplete;
              this.renderRoot.querySelector<HTMLInputElement>(`#wake-${i}`)?.focus();
            }}
          >
            ${icon(ICON.clock)}${wakeText}
          </button>`
      : nothing;

    return html`
      <div class="night">
        <div class="row">${programToggle}${wake}</div>
        ${this._spark(v, on && usable, i)}
      </div>
    `;
  }

  /** The night curve from bedtime to wake, coloured by temperature, with a "now" marker while the program runs. */
  private _spark(v: SideView, running: boolean, i: number): TemplateResult {
    const wakeMinute = running ? (v.night?.wakeMinute ?? null) : null;
    // Not running: preview a night from now to the next wake time.
    const previewWake =
      v.wake?.minuteOfDay != null
        ? ((v.wake.minuteOfDay - minuteOfDay(this.now ?? new Date(), this.hass?.config?.time_zone) + 1440) % 1440 || 1440)
        : null;
    const end = running ? wakeMinute : previewWake;
    const pts = sampleNight(this._schedule, end, 5);
    const temps = pts.map((p) => p[1]);
    const lo = Math.min(...temps) - 0.5;
    const hi = Math.max(...temps) + 0.5;
    const span = pts[pts.length - 1][0];
    const W = 100;
    const H = 40;
    const x = (m: number) => (m / span) * W;
    const y = (c: number) => 3 + (1 - (c - lo) / (hi - lo)) * (H - 6);
    const line = pts.map(([m, c], k) => `${k ? "L" : "M"}${x(m).toFixed(2)},${y(c).toFixed(2)}`).join("");
    const area = `${line}L${W},${H}L0,${H}Z`;
    const stops = this._dark ? NIGHT_STOPS : INK_STOPS;
    const gid = `obc-curve-${i}`;
    const grad = [0, 0.25, 0.5, 0.75, 1].map((f) => {
      const c = hi - f * (hi - lo);
      return svg`<stop offset=${f} stop-color=${tempColor(c, stops)}></stop>`;
    });
    const fillGrad = [0, 1].map((f) => svg`<stop offset=${f} stop-color=${tempColor(hi - f * (hi - lo))} stop-opacity=${f ? 0 : 0.35}></stop>`);

    const n = running ? v.night : null;
    const marker =
      n && n.setpoint !== null && n.minute <= span
        ? html`<div class="elapsed" style=${`width:${x(n.minute)}%`}></div>
            <div class="marker" style=${`left:${x(n.minute)}%;top:${(y(n.setpoint) / H) * 100}%`}></div>`
        : nothing;

    const fmtHours = (m: number) => `${Math.floor(m / 60)}h${m % 60 ? String(Math.round(m % 60)).padStart(2, "0") : ""}`;
    const label = running && n
      ? `Night program, ${Math.round(n.minute)} min in, curve ${n.setpoint === null ? "done" : n.setpoint.toFixed(1) + " °C"}`
      : "Night curve preview";

    return html`
      <div class="spark ${running ? "" : "dim"}" role="img" aria-label=${label}>
        <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <linearGradient id=${gid} x1="0" y1="0" x2="0" y2="1">${grad}</linearGradient>
            <linearGradient id=${gid + "f"} x1="0" y1="0" x2="0" y2="1">${fillGrad}</linearGradient>
          </defs>
          <path d=${area} fill=${`url(#${gid}f)`}></path>
          <path d=${line} fill="none" stroke=${`url(#${gid})`} stroke-width="2" vector-effect="non-scaling-stroke" stroke-linejoin="round"></path>
        </svg>
        ${marker}
      </div>
      <div class="spark-axis num" aria-hidden="true">
        <span>${running && n ? "bed" : "now"}</span>
        <span>${n && n.setpoint !== null ? `${n.setpoint.toFixed(1)}°` : `${Math.min(...temps).toFixed(0)}–${Math.max(...temps).toFixed(0)}°`}</span>
        <span>${end === null ? `+${fmtHours(span)}` : "wake"}</span>
      </div>
    `;
  }
}
