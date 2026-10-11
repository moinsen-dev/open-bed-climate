import { describe, expect, it } from "vitest";
import { contrast, INK_STOPS, NIGHT_STOPS, sideColors, tempColor } from "../src/color";

describe("temperature colour scale", () => {
  it("hits the DESIGN.md stops and clamps outside 13–43 °C", () => {
    expect(tempColor(13)).toBe("#4C9BFF");
    expect(tempColor(20)).toBe("#5CD3F0");
    expect(tempColor(28)).toBe("#D8E4EC");
    expect(tempColor(36)).toBe("#FFB547");
    expect(tempColor(43)).toBe("#FF8F4A");
    expect(tempColor(5)).toBe("#4C9BFF");
    expect(tempColor(60)).toBe("#FF8F4A");
  });

  it("interpolates between stops", () => {
    expect(tempColor(24)).toBe("#9ADCEE"); // halfway 20 -> 28
  });

  it("text colours stay readable on both themes across the whole range", () => {
    for (let t = 13; t <= 43; t += 0.5) {
      // Light themes: white card (HA default) and the dawn surface.
      expect(contrast(tempColor(t, INK_STOPS), "#FFFFFF")).toBeGreaterThanOrEqual(4.5);
      // Dark themes: HA default dark card and the Thermal Night surface.
      expect(contrast(tempColor(t, NIGHT_STOPS), "#1C1C1C")).toBeGreaterThanOrEqual(4.5);
      expect(contrast(tempColor(t, NIGHT_STOPS), "#0E1528")).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("sideColors picks the ink scale for the theme", () => {
    expect(sideColors(null, true)).toBeNull();
    expect(sideColors(20, true)).toEqual({ fill: "#5CD3F0", ink: "#5CD3F0" });
    expect(sideColors(20, false)).toEqual({ fill: "#5CD3F0", ink: "#0A6E8C" });
  });
});
