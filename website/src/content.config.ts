import { existsSync, readFileSync } from "node:fs";
import { defineCollection } from "astro:content";
import { glob, file } from "astro/loaders";
import { z } from "astro/zod";
import { parse } from "smol-toml";
import { kitSchema, partRoleSchema, featureSchema, featureNameSchema } from "./lib/schemas.ts";
import { featuresLoader } from "./lib/features.ts";
import { DOC_FILES, docId, BUILD_FILES, buildId } from "./lib/docs-map.ts";

// Paths are relative to website/, so ".." is the repo root. The repo is the CMS.

// Kits: one TOML file per entry. id = filename stem (solo-starter, duo-standard, duo-reference).
const kits = defineCollection({
  loader: glob({ pattern: "*.toml", base: "../hardware/kits", generateId: ({ entry }) => entry.replace(/\.toml$/, "") }),
  schema: kitSchema,
});

// Parts: top level is { role: [...] }; unwrap it so each role is one entry.
const parts = defineCollection({
  loader: file("../hardware/parts.toml", { parser: (text) => (parse(text) as { role: Record<string, unknown>[] }).role }),
  schema: partRoleSchema,
});

// Capability table parsed out of docs/FEATURES.md.
const features = defineCollection({ loader: featuresLoader("../docs/FEATURES.md"), schema: featureSchema });

// Repo docs rendered in place (no frontmatter; the title comes from the first heading).
const docs = defineCollection({
  loader: glob({ pattern: DOC_FILES, base: "..", generateId: ({ entry }) => docId(entry) }),
});

// Build guide (docs/build): overview + numbered steps, rendered in place under /build/.
const build = defineCollection({
  loader: glob({ pattern: BUILD_FILES, base: "../docs/build", generateId: ({ entry }) => buildId(entry) }),
});

// Hand-maintained site data, each entry with a `source` pointer.
const roadmap = defineCollection({
  loader: file("src/data/roadmap.yaml"),
  schema: z.object({ id: z.string(), area: z.string(), state: z.enum(["done", "next", "measure"]), text: z.string(), source: z.string() }),
});
const helpWanted = defineCollection({
  loader: file("src/data/help-wanted.yaml"),
  schema: z.object({
    id: z.string(),
    role: z.enum(["builder", "parts", "electronics", "mechanical", "firmware", "software", "research", "docs"]),
    task: z.string(),
    source: z.string(),
    link: z.string(),
    difficulty: z.enum(["easy", "medium", "hard"]),
  }),
});
const sponsorAsks = defineCollection({
  loader: file("src/data/sponsor-asks.yaml"),
  schema: z.object({ id: z.string(), ask: z.string(), unlocks: z.string(), range: z.string(), source: z.string() }),
});
const featureNames = defineCollection({ loader: file("src/data/feature-names.yaml"), schema: featureNameSchema });
const issueTemplates = defineCollection({
  loader: glob({ pattern: ["*.yml", "!config.yml"], base: "../.github/ISSUE_TEMPLATE", generateId: ({ entry }) => entry }),
  schema: z.object({ name: z.string(), description: z.string().optional() }),
});
const sponsors = defineCollection({
  loader: file("src/data/sponsors.yaml"),
  schema: z.object({ id: z.string(), name: z.string(), tier: z.string(), url: z.url().optional() }),
});

// Build log (RSS).
const log = defineCollection({
  loader: glob({ pattern: "*.md", base: "src/content/log" }),
  schema: z.object({ title: z.string(), date: z.coerce.date(), summary: z.string() }),
});

// Contributors from .all-contributorsrc (all-contributors spec). Avatars are not fetched while the repo is
// unpublished; once they are, they must be downloaded at build time and self-hosted (02-community §3.4).
const contributors = defineCollection({
  loader: {
    name: "all-contributors",
    load: async ({ store, logger }) => {
      store.clear();
      const path = "../.all-contributorsrc";
      if (!existsSync(path)) {
        logger.info("no .all-contributorsrc yet; /community/ shows the empty state");
        return;
      }
      const rc = JSON.parse(readFileSync(path, "utf8")) as { contributors?: { login: string; name?: string; contributions?: string[] }[] };
      for (const c of rc.contributors ?? []) {
        store.set({ id: c.login, data: { login: c.login, name: c.name ?? c.login, contributions: c.contributions ?? [] } });
      }
    },
  },
  schema: z.object({ login: z.string(), name: z.string(), contributions: z.array(z.string()) }),
});

export const collections = {
  kits,
  parts,
  features,
  docs,
  build,
  roadmap,
  helpWanted,
  sponsorAsks,
  featureNames,
  issueTemplates,
  sponsors,
  log,
  contributors,
};
