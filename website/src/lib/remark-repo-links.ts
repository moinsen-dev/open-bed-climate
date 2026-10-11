// Rewrites relative links in repo Markdown rendered on the site (SAFETY.md, design docs, …).
// A link that pointed at a sibling file in the repo would 404 on the site, so it is resolved against the source
// file's repo path and sent to the matching site page, or to the file on the repo host.
// Runs as a Sätteri mdast plugin (Astro 7's default Markdown processor).
import { posix, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { REPO_URL } from "../site.ts";
import { docId, isRenderedDoc } from "./docs-map.ts";

const REPO_ROOT = resolve(process.cwd(), "..");

export function siteHrefForRepoPath(target: string, hash: string): string {
  if (isRenderedDoc(target)) return `/docs/${docId(target)}/${hash}`;
  const kit = /^hardware\/kits\/([^/]+)\.toml$/.exec(target);
  if (kit) return `/kits/${kit[1]}/${hash}`;
  if (target === "hardware/parts.toml" || target === "hardware/PARTS.md") return `/parts/${hash}`;
  if (target === "docs/FEATURES.md") return `/features/${hash}`;
  const clean = target.replace(/\/$/, "");
  const isFile = /\.[A-Za-z0-9]+$/.test(clean);
  return `${REPO_URL}/${isFile ? "blob" : "tree"}/main/${clean}${hash}`;
}

/** New URL for a link found in the repo file `srcRepoPath`, or null to leave it unchanged. */
export function rewriteRepoLink(url: string, srcRepoPath: string): string | null {
  if (/^([a-z][a-z0-9+.-]*:|#|\/)/i.test(url)) return null; // absolute, anchor-only or site-rooted
  const [path, ...rest] = url.split("#");
  const hash = rest.length ? `#${rest.join("#")}` : "";
  const target = posix.normalize(posix.join(posix.dirname(srcRepoPath), path));
  if (target.startsWith("..")) return null;
  return siteHrefForRepoPath(target, hash);
}

interface UrlNode { url: string }
interface Ctx { setProperty(node: UrlNode, key: "url", value: string): void }

/** Sätteri plugin factory: active only for repo files outside website/. */
export default function repoLinks({ fileURL }: { fileURL: URL | undefined }) {
  if (!fileURL) return null;
  const rel = relative(REPO_ROOT, fileURLToPath(fileURL)).split("\\").join("/");
  if (rel.startsWith("..") || rel.startsWith("website/")) return null;
  const fix = (node: UrlNode, ctx: Ctx) => {
    const next = rewriteRepoLink(node.url, rel);
    if (next !== null) ctx.setProperty(node, "url", next);
  };
  return { name: "repo-links", link: fix, image: fix, definition: fix };
}
