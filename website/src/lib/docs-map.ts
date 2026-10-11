// Which repo Markdown files are rendered in place on the site (everything else links to the repo).
// OPEN-DECISIONS.md and BOM.md are deliberately excluded: OPEN-DECISIONS has a section that stays off the site
// (01-content C8) and BOM.md v0.1 carries stale voltage and price figures (C2, C3). They link to the repo instead.
export const DOC_FILES = ["SAFETY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "docs/design/0*.md", "hardware/WIRING.md"];

const DOC_RE = /^(SAFETY|CONTRIBUTING|CODE_OF_CONDUCT)\.md$|^docs\/design\/0[^/]*\.md$|^hardware\/WIRING\.md$/;

/** Route id for a repo path in the docs set: safety, design/00-architecture, hardware/wiring. */
export const docId = (repoPath: string) => repoPath.replace(/^docs\//, "").replace(/\.md$/, "").toLowerCase();
export const isRenderedDoc = (repoPath: string) => DOC_RE.test(repoPath);

// Build guide: docs/build/README.md → /build/, docs/build/01-tools-and-safety.md → /build/01-tools-and-safety/.
export const BUILD_FILES = ["README.md", "0*.md"];
export const buildId = (file: string) => (file === "README.md" ? "overview" : file.replace(/\.md$/, ""));
export function buildHref(repoPath: string): string | null {
  const m = /^docs\/build\/(README|0[^/]*)\.md$/.exec(repoPath);
  if (!m) return null;
  return m[1] === "README" ? "/build/" : `/build/${m[1]}/`;
}
