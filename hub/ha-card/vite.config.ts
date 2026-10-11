import { defineConfig } from "vitest/config";

// One self-contained ES module for Home Assistant (/config/www/open-bed-climate-card.js): Lit is bundled, no
// runtime imports. `npm run dev` serves dev/index.html, a harness with a mocked `hass`.
export default defineConfig({
  build: {
    target: "es2022",
    lib: {
      entry: "src/index.ts",
      formats: ["es"],
      fileName: () => "open-bed-climate-card.js",
    },
    rolldownOptions: {
      output: {
        codeSplitting: false,
        minify: true,
        postBanner:
          "/*! open-bed-climate-card · Apache-2.0 · https://github.com/moinsen-dev/open-bed-climate\n" +
          " * Includes Lit (https://lit.dev), Copyright 2017 Google LLC, BSD-3-Clause. */",
      },
    },
  },
  test: { include: ["test/**/*.test.ts"], environment: "node" },
});
