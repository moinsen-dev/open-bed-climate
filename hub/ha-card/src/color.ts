// "Thermal Night" temperature scale (DESIGN.md): temperature is the only colour, cold cyan to warm amber over the
// real 13–43 °C setpoint range. Night stops are for fills and for text on dark cards; ink stops are darker
// variants for text on light cards (WCAG AA on white).

export const T_MIN = 13;
export const T_MAX = 43;

type Stop = readonly [number, string];

/** DESIGN.md temp-13 … temp-43. */
export const NIGHT_STOPS: readonly Stop[] = [
  [13, "#4C9BFF"],
  [20, "#5CD3F0"],
  [28, "#D8E4EC"],
  [36, "#FFB547"],
  [43, "#FF8F4A"],
];

/** Light-theme text: dawn-cold / dawn-ink-muted / dawn-warm, extended to the ends of the range. */
export const INK_STOPS: readonly Stop[] = [
  [13, "#1C5BB5"],
  [20, "#0A6E8C"],
  [28, "#4A5670"],
  [36, "#9C5200"],
  [43, "#A63F12"],
];

export type Rgb = readonly [number, number, number];

export function hexToRgb(hex: string): Rgb {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export function rgbToHex([r, g, b]: Rgb): string {
  return "#" + [r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("").toUpperCase();
}

/** Colour for a temperature, linear in sRGB between stops, clamped to the range. */
export function tempColor(c: number, stops: readonly Stop[] = NIGHT_STOPS): string {
  const t = Math.min(T_MAX, Math.max(T_MIN, c));
  for (let i = 1; i < stops.length; i++) {
    const [t1, h1] = stops[i];
    if (t <= t1) {
      const [t0, h0] = stops[i - 1];
      const f = (t - t0) / (t1 - t0);
      const a = hexToRgb(h0);
      const b = hexToRgb(h1);
      return rgbToHex([a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f]);
    }
  }
  return stops[stops.length - 1][1];
}

/** WCAG relative luminance. */
export function luminance(hex: string): number {
  const lin = hexToRgb(hex).map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

export function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/** Colours a side needs: `fill` for the tint and the curve, `ink` for temperature text on the current theme. */
export function sideColors(c: number | null, dark: boolean): { fill: string; ink: string } | null {
  if (c === null) return null;
  return { fill: tempColor(c, NIGHT_STOPS), ink: tempColor(c, dark ? NIGHT_STOPS : INK_STOPS) };
}
