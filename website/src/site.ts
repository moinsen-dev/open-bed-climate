// Site-wide constants. Owner decisions (repo, domain, contact, legal pages) live here and nowhere else.

export const SITE_NAME = "Open Bed Climate";
export const SITE_TAGLINE = "Sleep at your temperature. On your hardware.";
export const SITE_DESCRIPTION =
  "An open-source, local-first bed climate system: water cools and warms each side of the bed, built from standard parts you can buy, repair and change. Design phase.";

export const SITE_URL = "https://openbedclimate.moinsen.dev"; // also the default in astro.config.mjs and public/robots.txt

export const REPO_URL = "https://github.com/moinsen-dev/open-bed-climate";
export const repoBlob = (path: string) => `${REPO_URL}/blob/main/${path}`;
export const repoTree = (path: string) => `${REPO_URL}/tree/main/${path}`;
export const issueTemplate = (file: string) => `${REPO_URL}/issues/new?template=${file}`;

// Contact for sponsors, press and safety. Sponsorship goes through e-mail for now.
export const CONTACT_EMAIL = "business@moinsen.dev";
export const SPONSOR_MAILTO = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent("Open Bed Climate sponsorship")}`;

// Legal pages live on the owner's main site. /impressum/ redirects there (public/_redirects);
// /privacy/ is only a short site-specific supplement.
export const IMPRESSUM_URL = "https://www.moinsen.dev/en/impressum";
export const PRIVACY_URL = "https://www.moinsen.dev/en/privacy";

// Newsletter (listmonk) is not set up. The form renders only when this is set.
export const NEWSLETTER_URL: string | null = null;

// Community home: GitHub Discussions (02-community §3.1).
export const DISCUSSIONS_URL = `${REPO_URL}/discussions`;

export const NAV = [
  { href: "/how-it-works/", label: "How it works" },
  { href: "/kits/", label: "Kits" },
  { href: "/build/", label: "Build" },
  { href: "/docs/safety/", label: "Safety" },
  { href: "/status/", label: "Status" },
  { href: "/contribute/", label: "Contribute" },
];

export const FOOTER_NAV = [
  {
    title: "Build",
    links: [
      { href: "/build/", label: "Build guide" },
      { href: "/kits/solo-starter/shopping/", label: "Shopping list" },
      { href: "/kits/", label: "Kits" },
      { href: "/parts/", label: "Parts" },
      { href: "/parts/carrier-pcb/", label: "Carrier PCB" },
      { href: "/docs/safety/", label: "Safety" },
      { href: "/docs/hardware/wiring/", label: "Wiring" },
      { href: "/install/", label: "Install firmware" },
    ],
  },
  {
    title: "Learn",
    links: [
      { href: "/how-it-works/", label: "How it works" },
      { href: "/features/", label: "Features" },
      { href: "/schedule/", label: "Schedule" },
      { href: "/docs/", label: "Docs" },
    ],
  },
  {
    title: "Project",
    links: [
      { href: "/status/", label: "Status" },
      { href: "/contribute/", label: "Contribute" },
      { href: "/community/", label: "Community" },
      { href: "/sponsor/", label: "Sponsor" },
      { href: "/log/", label: "Build log" },
      { href: "/about/", label: "About" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "/docs/code_of_conduct/", label: "Code of Conduct" },
      { href: "/about/#licenses", label: "Licenses" },
      { href: IMPRESSUM_URL, label: "Impressum" },
      { href: PRIVACY_URL, label: "Privacy policy" },
      { href: "/privacy/", label: "Privacy on this site" },
    ],
  },
];

export const MODULE_ORDER = ["Power", "Control", "Hub", "Thermal", "Water mat", "Sensing", "Add-ons"];

// Words, never emoji (01-content §6).
export const STATUS_LABEL = {
  now: "Designed",
  planned: "Planned",
  third_party: "Via other products",
  out_of_scope: "Out of scope (by design)",
  done: "Done",
  next: "Next",
  measure: "Help wanted",
} as const;

export const PART_STATUS_LABEL = {
  datasheet: "Datasheet",
  listing: "Listing only",
  unverified: "Unverified",
  rejected: "Rejected",
} as const;

export const SENSING_LABEL: Record<string, string> = {
  none: "None",
  load_cells: "Load cells",
  pneumatic: "Pneumatic",
  piezo_grid: "Piezo grid",
};

export const LICENSES = {
  software: "Apache-2.0",
  hardware: "CERN-OHL-S-2.0",
  siteContent: "Apache-2.0 unless noted",
};

// Hero/demo assumption for the default night program (04-design §6).
export const HERO_BEDTIME_MIN_OF_DAY = 23 * 60;
export const HERO_WAKE_OFFSET_MIN = 480;
