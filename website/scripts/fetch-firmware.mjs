// Before every build (npm "prebuild"): put the latest firmware release into public/firmware/ (gitignored), so
// /install/ serves it same-origin (the CSP allows no third-party requests, and Web Serial flashing needs the bytes).
//
//   public/firmware/release.json                 what /install/ renders from (tag, files, checksums)
//   public/firmware/SHA256SUMS
//   public/firmware/hub/manifest.json            ESP Web Tools manifest
//   public/firmware/hub/opod-hub-factory.bin
//   public/firmware/pico2/opod-pico2-<kit>.uf2
//
// Source: the latest GitHub release (assets built by .github/workflows/release.yml), every file checked against
// its SHA256SUMS. Uses github.com release URLs, not the API, so there is no rate limit on shared build machines.
// Never fails the build: with no release, no network or a bad download, public/firmware/ is left without
// release.json and /install/ says "no release yet" (after a network error, a complete earlier download is kept).
//
// Env: FIRMWARE_DIR=<dir>  use local files (release.yml names + SHA256SUMS) instead of downloading, e.g. to test
//      FIRMWARE_TAG=<tag>  label for FIRMWARE_DIR (default "local")
//      FIRMWARE_OFFLINE=1  don't touch the network
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const REPO = "https://github.com/moinsen-dev/open-bed-climate"; // = REPO_URL in src/site.ts
const OUT = new URL("../public/firmware/", import.meta.url).pathname;
const KITS = ["solo-starter", "duo-standard", "duo-reference"]; // hardware/kits/*.toml with a firmware build
const HUB = "opod-hub-factory.bin";
const FILES = [HUB, ...KITS.map((k) => `opod-pico2-${k}.uf2`)];
const PROJECT = "moinsen-dev.open-bed-climate"; // esphome.project.name in hub/esphome/opod-hub-factory.yaml
const TIMEOUT_MS = 20_000;

const log = (msg) => console.log(`fetch-firmware: ${msg}`);
const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");

async function get(url, opts = {}) {
  return fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS), ...opts });
}

async function latestTag() {
  // /releases/latest redirects to /releases/tag/<tag>; without a release it redirects to /releases.
  const res = await get(`${REPO}/releases/latest`, { redirect: "manual" });
  const m = /\/releases\/tag\/([^/?#]+)$/.exec(res.headers.get("location") ?? "");
  return m ? decodeURIComponent(m[1]) : null;
}

async function download(tag) {
  const base = `${REPO}/releases/download/${encodeURIComponent(tag)}/`;
  const files = {};
  for (const name of ["SHA256SUMS", ...FILES]) {
    const res = await get(base + name);
    if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
    files[name] = Buffer.from(await res.arrayBuffer());
  }
  return files;
}

function readLocal(dir) {
  return Object.fromEntries(["SHA256SUMS", ...FILES].map((n) => [n, readFileSync(join(dir, n))]));
}

function verify(files) {
  const sums = new Map(
    files.SHA256SUMS.toString("utf8").trim().split("\n").map((l) => {
      const [hash, name] = l.trim().split(/\s+\*?/);
      return [name, hash];
    }),
  );
  for (const name of FILES) {
    if (!sums.has(name)) throw new Error(`${name} missing from SHA256SUMS`);
    if (sums.get(name) !== sha256(files[name])) throw new Error(`${name}: checksum mismatch`);
  }
}

function write(tag, files) {
  const tmp = OUT.replace(/\/$/, "") + ".tmp/";
  rmSync(tmp, { recursive: true, force: true });
  mkdirSync(join(tmp, "hub"), { recursive: true });
  mkdirSync(join(tmp, "pico2"), { recursive: true });
  writeFileSync(join(tmp, "SHA256SUMS"), files.SHA256SUMS);
  writeFileSync(join(tmp, "hub", HUB), files[HUB]);
  writeFileSync(
    join(tmp, "hub", "manifest.json"),
    JSON.stringify(
      {
        name: PROJECT, // must match what the device reports over Improv, so updates are recognised as such
        version: tag,
        home_assistant_domain: "esphome",
        new_install_prompt_erase: true,
        builds: [{ chipFamily: "ESP32-S3", parts: [{ path: HUB, offset: 0 }] }],
      },
      null,
      2,
    ),
  );
  for (const k of KITS) writeFileSync(join(tmp, "pico2", `opod-pico2-${k}.uf2`), files[`opod-pico2-${k}.uf2`]);
  const meta = {
    tag,
    url: `${REPO}/releases/tag/${encodeURIComponent(tag)}`,
    hub: { path: `/firmware/hub/${HUB}`, manifest: "/firmware/hub/manifest.json", size: files[HUB].length, sha256: sha256(files[HUB]) },
    pico2: Object.fromEntries(
      KITS.map((k) => {
        const n = `opod-pico2-${k}.uf2`;
        return [k, { path: `/firmware/pico2/${n}`, file: n, size: files[n].length, sha256: sha256(files[n]) }];
      }),
    ),
  };
  writeFileSync(join(tmp, "release.json"), JSON.stringify(meta, null, 2) + "\n");
  rmSync(OUT, { recursive: true, force: true });
  renameSync(tmp, OUT);
  log(`${tag}: ${FILES.length} files + SHA256SUMS verified -> public/firmware/`);
}

function keepOrClear(reason, keep = true) {
  if (keep && existsSync(join(OUT, "release.json"))) {
    log(`${reason}; keeping the earlier download in public/firmware/`);
  } else {
    rmSync(OUT, { recursive: true, force: true });
    log(`${reason}; /install/ will show "no release yet"`);
  }
}

try {
  if (process.env.FIRMWARE_DIR) {
    const files = readLocal(process.env.FIRMWARE_DIR);
    verify(files);
    write(process.env.FIRMWARE_TAG ?? "local", files);
  } else if (process.env.FIRMWARE_OFFLINE) {
    keepOrClear("FIRMWARE_OFFLINE set");
  } else {
    const tag = await latestTag();
    if (!tag) keepOrClear("no release published", false);
    else {
      const files = await download(tag);
      verify(files);
      write(tag, files);
    }
  }
} catch (e) {
  if (process.env.FIRMWARE_DIR) throw e; // a local test run should fail loudly
  keepOrClear(`no usable release (${e.message})`);
}
