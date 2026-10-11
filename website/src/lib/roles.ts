// Contributor roles (01-content §5, CONTRIBUTING). `id` is the /contribute/#anchor and the help-wanted.yaml role.
export const ROLES = [
  { id: "builder", title: "Builders", skills: "Hands-on, careful, patient. Basic electronics.", next: { label: "Post a build report", template: "build-report.yml" } },
  { id: "parts", title: "Parts hunters", skills: "Datasheets, distributors, regional sourcing. No coding.", next: { label: "Suggest or verify a part", template: "part-substitution.yml" } },
  { id: "electronics", title: "Electronics & safety", skills: "Power electronics, protection, PCB design, safety review.", next: { label: "Report a safety concern", template: "safety-concern.yml" } },
  { id: "mechanical", title: "Mechanical & textile", skills: "TPU welding, fluid couplings, enclosures, CAD.", next: null },
  { id: "firmware", title: "Firmware", skills: "Rust, embassy, RP2350, no_std.", next: null },
  { id: "software", title: "Home Assistant & software", skills: "ESPHome, C++, Python, Home Assistant automations.", next: null },
  { id: "research", title: "Researchers", skills: "Thermal measurement, signal processing, sleep science.", next: null },
  { id: "docs", title: "Writers & translators", skills: "Clear English, or a translation into your language.", next: null },
] as const;
