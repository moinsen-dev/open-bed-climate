import { z } from "astro/zod"; // Zod 4, re-exported by Astro; no separate zod dependency

export const SENSING = ["none", "load_cells", "pneumatic", "piezo_grid"] as const; // = opod.kit.SENSING_OPTIONS
export const PART_STATUS = ["datasheet", "listing", "unverified", "rejected"] as const; // = render_parts.BADGE keys

// Mirrors opod.kit.load_kit. Top level is strict: same rule as ALLOWED_TOP.
// Inner tables are not strict, because Python only rejects unknown *sections*. FORBIDDEN_KEYS stay Python's job (CI).
export const kitSchema = z.strictObject({
  kit: z.object({
    name: z.string(),
    tier: z.union([z.literal(0), z.literal(1)]),
    zones: z.union([z.literal(1), z.literal(2)]),
  }),
  thermal: z.object({
    tec_per_zone: z.int().min(1).max(6),
    heatsink_k_per_w: z.number().positive(),
    max_tec_current_a: z.number().min(1).max(6), // MAX_TEC_CURRENT_A
  }),
  sensing: z.object({ option: z.enum(SENSING) }),
  power: z.object({ tec_psu_w_per_zone: z.number().positive(), aux_psu_w: z.number().positive() }),
  claims: z.object({ min_water_c: z.number(), max_water_c: z.number().max(43) }),
});
export type KitData = z.infer<typeof kitSchema>;

const partExample = z
  .object({
    name: z.string(),
    status: z.enum(PART_STATUS),
    // Unverified examples may have no source or date yet (parts.toml uses ""); render_parts enforces the rest.
    source: z.union([z.url(), z.literal("")]),
    verified_on: z.union([z.iso.date(), z.literal("")]),
    notes: z.string().optional(),
  })
  .refine((e) => (e.status !== "datasheet" && e.status !== "listing") || (e.source !== "" && e.verified_on !== ""), {
    message: "datasheet/listing examples need a source and verified_on",
  });

export const partRoleSchema = z.object({
  id: z.string(),
  module: z.string(), // ordered by MODULE_ORDER in src/site.ts; unknown modules go last
  safety: z.boolean(),
  requirement: z.string(),
  notes: z.string().optional(),
  example: z.array(partExample).default([]),
});
export type PartRole = z.infer<typeof partRoleSchema>;

export const FEATURE_STATE = { "✅": "now", "🔜": "planned", "🔌": "third_party", "❌": "out_of_scope" } as const;
export type FeatureState = (typeof FEATURE_STATE)[keyof typeof FEATURE_STATE];
export const featureSchema = z.object({
  row: z.int(), // 0-based order in the FEATURES.md table (feature-names.yaml is keyed by it)
  pod: z.string(), // column 1. Kept for the row-count check, never rendered (01-content C6)
  approach: z.string(), // markdown, rendered inline
  module: z.string(),
  status: z.array(z.object({ state: z.enum(["now", "planned", "third_party", "out_of_scope"]), note: z.string() })),
});

export const featureNameSchema = z.object({
  id: z.string(),
  row: z.int(),
  name: z.string(),
  // Optional rewrite of the approach cell when the repo text must not render raw (01-content C6/C9).
  approach: z.string().optional(),
});

// hardware/shopping/*.toml (mirrors opod.shopping.load; Python stays the authority, CI runs both).
export const SHOP_STAGES = ["bench", "bed", "tool"] as const;
export const shoppingSchema = z.strictObject({
  list: z.object({
    kit: z.string(),
    currency: z.string(),
    checked_on: z.iso.date(),
    region: z.string(),
    notes: z.string(),
  }),
  item: z.array(
    z
      .object({
        role: z.string(),
        name: z.string(),
        qty: z.int().min(0),
        pack: z.int().min(1).default(1),
        unit_eur: z.number().min(0),
        shop: z.string(),
        url: z.url().startsWith("https://"),
        status: z.enum(["listing", "estimate"]),
        stage: z.enum(SHOP_STAGES),
        notes: z.string().default(""),
      })
      .refine((i) => (i.role === "tool") === (i.stage === "tool"), { message: "tools (and only tools) go in stage 'tool'" }),
  ),
});
export type ShoppingData = z.infer<typeof shoppingSchema>;
