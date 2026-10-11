// Which repo Markdown files are rendered in place under /docs/ (everything else links to the repo).
// OPEN-DECISIONS.md and BOM.md are deliberately excluded: OPEN-DECISIONS has a section that stays off the site
// (01-content C8) and BOM.md v0.1 carries stale voltage and price figures (C2, C3). They link to the repo instead.
export const DOC_FILES = ["SAFETY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "docs/design/0*.md", "hardware/WIRING.md"];

const DOC_RE = /^(SAFETY|CONTRIBUTING|CODE_OF_CONDUCT)\.md$|^docs\/design\/0[^/]*\.md$|^hardware\/WIRING\.md$/;

/** Route id for a repo path in the docs set: safety, design/00-architecture, hardware/wiring. */
export const docId = (repoPath: string) => repoPath.replace(/^docs\//, "").replace(/\.md$/, "").toLowerCase();
export const isRenderedDoc = (repoPath: string) => DOC_RE.test(repoPath);
