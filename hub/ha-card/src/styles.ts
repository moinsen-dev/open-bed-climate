import { css } from "lit";

// Text, surfaces and lines come from the Home Assistant theme; the only accent is the temperature colour of each
// side (--fill for tints and the curve, --ink for temperature text on the current theme), set per side.
export const styles = css`
  :host {
    --obc-text: var(--primary-text-color, #1c1c1c);
    --obc-muted: var(--secondary-text-color, #6b778e);
    --obc-line: var(--divider-color, rgba(127, 127, 127, 0.25));
    --obc-error: var(--error-color, #db4437);
    --obc-surface: var(--ha-card-background, var(--card-background-color, #fff));
    display: block;
  }
  ha-card {
    padding: 14px 14px 12px;
    color: var(--obc-text);
    overflow: hidden;
  }
  button {
    font: inherit;
    color: inherit;
    background: none;
    border: 0;
    padding: 0;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
  }
  button:disabled {
    cursor: default;
    opacity: 0.4;
  }
  button:focus-visible,
  input:focus-visible {
    outline: 2px solid var(--obc-text);
    outline-offset: 2px;
  }
  svg.icon {
    width: 18px;
    height: 18px;
    fill: currentColor;
    flex: none;
  }
  .caps {
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--obc-muted);
  }
  .num {
    font-variant-numeric: tabular-nums;
  }

  /* Header */
  header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 2px 12px;
    min-height: 28px;
  }
  header h2 {
    margin: 0;
    flex: 1;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: -0.005em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid var(--obc-line);
    font-size: 0.75rem;
    color: var(--obc-muted);
    white-space: nowrap;
  }
  .pill .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
  }
  .pill.bad {
    color: var(--obc-error);
    border-color: color-mix(in srgb, var(--obc-error) 45%, transparent);
  }
  .pill.action:hover {
    color: var(--obc-text);
    border-color: var(--obc-muted);
  }

  /* The bed: a headboard and a mattress split into sides */
  .bed {
    position: relative;
  }
  .headboard {
    height: 14px;
    margin: 0 8px -1.5px;
    border: 1.5px solid var(--obc-line);
    border-bottom: 0;
    border-radius: 14px 14px 0 0;
    background: color-mix(in srgb, var(--obc-text) 4%, transparent);
  }
  .mattress {
    display: grid;
    grid-template-columns: repeat(var(--sides, 2), minmax(0, 1fr));
    grid-template-rows: repeat(var(--rows, 6), auto);
    border: 1.5px solid var(--obc-line);
    border-radius: 20px 20px 26px 26px;
    overflow: hidden;
  }
  .side {
    --fill: var(--obc-muted);
    --ink: var(--obc-text);
    position: relative;
    /* Subgrid: the rows of both sides line up even when one shows a fault banner. */
    display: grid;
    grid-template-rows: subgrid;
    grid-row: span var(--rows, 6);
    align-items: start;
    row-gap: 12px;
    padding: 10px 12px 14px;
    background: linear-gradient(
      180deg,
      color-mix(in srgb, var(--fill) var(--tint-top, 30%), transparent) 0%,
      color-mix(in srgb, var(--fill) var(--tint-bottom, 6%), transparent) 100%
    );
    transition: background 1.2s ease;
    min-width: 0;
  }
  .side + .side {
    border-left: 1.5px dashed var(--obc-line);
  }
  .side.off {
    --tint-top: 12%;
    --tint-bottom: 2%;
  }
  .side.offline {
    --fill: var(--obc-muted);
    --tint-top: 6%;
    --tint-bottom: 2%;
    color: var(--obc-muted);
  }
  .pillow {
    justify-self: center;
    width: min(72%, 150px);
    height: 24px;
    border: 1.5px solid var(--obc-line);
    border-radius: 9px;
    display: grid;
    place-items: center;
    background: color-mix(in srgb, var(--obc-surface) 22%, transparent);
  }
  .pillow .caps {
    color: var(--obc-text);
    max-width: 92%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .side > .row,
  .side > .offline-note {
    align-self: center;
  }
  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-height: 32px;
  }
  .state {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    min-width: 0;
  }
  .state .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex: none;
    background: var(--obc-muted);
  }
  .state.running .dot {
    background: var(--ink);
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--fill) 60%, transparent);
    animation: breathe 3.2s ease-in-out infinite;
  }
  .state .caps {
    color: var(--obc-text);
  }
  @keyframes breathe {
    50% {
      box-shadow: 0 0 0 5px color-mix(in srgb, var(--fill) 0%, transparent);
    }
  }
  .icon-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    border: 1.5px solid var(--obc-line);
    color: var(--obc-muted);
    transition: color 0.2s, border-color 0.2s, background 0.2s;
    flex: none;
  }
  .icon-btn:not(:disabled):hover {
    color: var(--obc-text);
    border-color: var(--obc-muted);
  }
  .icon-btn.power[aria-pressed="true"] {
    color: var(--ink);
    border-color: color-mix(in srgb, var(--ink) 55%, transparent);
    background: color-mix(in srgb, var(--fill) 14%, transparent);
  }

  /* Readout */
  .readout {
    text-align: center;
    line-height: 1;
    padding: 2px 0 0;
  }
  .readout .big {
    font-size: 2.625rem;
    font-weight: 600;
    letter-spacing: -0.03em;
    color: var(--ink);
    transition: color 1.2s ease;
  }
  .readout .unit {
    font-size: 1rem;
    font-weight: 500;
    vertical-align: 0.9em;
    margin-left: 2px;
    color: var(--obc-muted);
  }
  .readout .caps {
    display: block;
    margin-top: 6px;
  }
  .readout .big.none {
    color: var(--obc-muted);
    font-weight: 400;
  }
  .side.offline .readout .big {
    color: var(--obc-muted);
  }

  /* Target stepper */
  .stepper {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 6px;
  }
  .stepper .value {
    text-align: center;
    line-height: 1.15;
  }
  .stepper .value strong {
    font-size: 1.25rem;
    font-weight: 600;
  }
  .stepper .value strong.pending {
    color: var(--ink);
  }
  .stepper .value .caps {
    display: block;
  }

  /* Night program */
  .night {
    align-self: start;
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding-top: 10px;
    border-top: 1px solid var(--obc-line);
  }
  .toggle {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 32px;
    font-size: 0.8125rem;
    font-weight: 500;
  }
  .toggle .track {
    position: relative;
    width: 32px;
    height: 18px;
    border-radius: 9px;
    border: 1.5px solid var(--obc-line);
    flex: none;
    transition: background 0.2s, border-color 0.2s;
  }
  .toggle .track::after {
    content: "";
    position: absolute;
    top: 2px;
    left: 2px;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: var(--obc-muted);
    transition: transform 0.2s, background 0.2s;
  }
  .toggle[aria-checked="true"] .track {
    border-color: color-mix(in srgb, var(--ink) 60%, transparent);
    background: color-mix(in srgb, var(--fill) 22%, transparent);
  }
  .toggle[aria-checked="true"] .track::after {
    transform: translateX(14px);
    background: var(--ink);
  }
  .wake {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 8px;
    margin-right: -6px;
    border-radius: 8px;
    font-size: 0.8125rem;
    color: var(--obc-muted);
    min-height: 32px;
  }
  .wake:not(:disabled):hover {
    color: var(--obc-text);
    background: color-mix(in srgb, var(--obc-text) 6%, transparent);
  }
  .wake svg.icon {
    width: 15px;
    height: 15px;
  }
  .wake-edit {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  input[type="time"] {
    font: inherit;
    font-size: 0.8125rem;
    color: var(--obc-text);
    background: transparent;
    border: 1.5px solid var(--obc-line);
    border-radius: 8px;
    padding: 4px 6px;
    min-height: 32px;
    box-sizing: border-box;
    color-scheme: var(--obc-scheme, light);
    width: 100%;
    min-width: 0;
  }

  .spark {
    position: relative;
    height: 46px;
  }
  .spark svg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    overflow: visible;
  }
  .spark .elapsed {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    background: color-mix(in srgb, var(--obc-text) 5%, transparent);
    border-right: 1.5px solid var(--ink);
  }
  .spark .marker {
    position: absolute;
    width: 9px;
    height: 9px;
    margin: -4.5px 0 0 -4.5px;
    border-radius: 50%;
    background: var(--ink);
    box-shadow: 0 0 0 3px var(--obc-surface);
  }
  .spark.dim svg {
    opacity: 0.45;
  }
  .spark-axis {
    display: flex;
    justify-content: space-between;
    font-size: 0.6875rem;
    color: var(--obc-muted);
    margin-top: -2px;
  }

  /* Details */
  .details {
    align-self: end;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 4px;
    text-align: center;
    padding-top: 10px;
    border-top: 1px solid var(--obc-line);
  }
  .details div {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
  }
  .details strong {
    font-size: 0.8125rem;
    font-weight: 600;
    white-space: nowrap;
  }
  .details .caps {
    font-size: 0.625rem;
    letter-spacing: 0.06em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Problem banner and offline notice */
  .banner {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 10px;
    border-radius: 12px;
    border: 1.5px solid color-mix(in srgb, var(--obc-error) 55%, transparent);
    background: color-mix(in srgb, var(--obc-error) 10%, var(--obc-surface));
    font-size: 0.8125rem;
    line-height: 1.35;
  }
  .banner .title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 600;
    color: var(--obc-error);
  }
  .banner .actions {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .text-btn {
    padding: 6px 12px;
    min-height: 32px;
    border-radius: 999px;
    border: 1.5px solid var(--obc-line);
    font-size: 0.8125rem;
    font-weight: 600;
  }
  .text-btn:hover {
    border-color: var(--obc-muted);
  }
  .text-btn.danger {
    color: var(--obc-surface);
    background: var(--obc-error);
    border-color: var(--obc-error);
  }
  .offline-note {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-height: 32px;
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--obc-muted);
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }

  /* One side: a single bed, a bit narrower */
  .bed.single {
    max-width: 320px;
    margin: 0 auto;
  }
  .bed.single .readout .big {
    font-size: 3rem;
  }

  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation: none !important;
      transition: none !important;
    }
  }
`;
