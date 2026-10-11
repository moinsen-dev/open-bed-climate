import { OpenBedClimateCard } from "./card";
import { OpenBedClimateCardEditor } from "./editor";

declare global {
  interface Window {
    customCards?: { type: string; name: string; description: string; preview?: boolean; documentationURL?: string }[];
  }
}

if (!customElements.get("open-bed-climate-card")) customElements.define("open-bed-climate-card", OpenBedClimateCard);
if (!customElements.get("open-bed-climate-card-editor")) customElements.define("open-bed-climate-card-editor", OpenBedClimateCardEditor);

window.customCards ??= [];
if (!window.customCards.some((c) => c.type === "open-bed-climate-card")) {
  window.customCards.push({
    type: "open-bed-climate-card",
    name: "Open Bed Climate",
    description: "Both sides of an Open Bed Climate bed: water temperature, target, night program and faults.",
    preview: true,
    documentationURL: "https://github.com/moinsen-dev/open-bed-climate/tree/main/hub/ha-card",
  });
}

export { OpenBedClimateCard, OpenBedClimateCardEditor };
