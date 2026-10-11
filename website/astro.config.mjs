import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import { satteri } from "@astrojs/markdown-satteri";
import repoLinks from "./src/lib/remark-repo-links.ts";

export default defineConfig({
  site: process.env.SITE_URL ?? "https://openbedclimate.moinsen.dev", // = SITE_URL in src/site.ts
  output: "static",
  trailingSlash: "always",
  build: { format: "directory", inlineStylesheets: "never" },
  markdown: {
    processor: satteri({ mdastPlugins: [repoLinks] }),
    // Shiki writes inline style="" attributes, which the CSP (style-src 'self') forbids. Code blocks are styled in CSS.
    syntaxHighlight: false,
  },
  vite: { build: { assetsInlineLimit: 0 } },
  integrations: [sitemap()],
});
