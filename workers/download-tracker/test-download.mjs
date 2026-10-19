// node workers/download-tracker/test-download.mjs
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import worker, { DEFAULT_ASSET } from "./src/index.js";

const here = new URL("./", import.meta.url);
const pyproject = readFileSync(new URL("../../pyproject.toml", here), "utf8");
const pyVersion = pyproject.match(/^version\s*=\s*"([^"]+)"/m)[1];
assert.equal(DEFAULT_ASSET, `zion-pattern-solver-${pyVersion}.tar.gz`, "default asset tracks pyproject version");

const env = {
  ASSETS: { fetch: async (req) => {
    const f = new URL("public" + new URL(req.url).pathname, here);
    return existsSync(f) ? new Response(readFileSync(f), { status: 200 }) : new Response("nf", { status: 404 });
  } },
  DOWNLOADS: { get: async () => null, put: async () => {}, list: async () => ({ keys: [] }) },
};
const ctx = { waitUntil() {} };
async function head(path) { return worker.fetch(new Request("https://t.example" + path, { method: "HEAD", headers: { "User-Agent": "Mozilla/5.0" } }), env, ctx); }

let r = await head("/download");
assert.equal(r.status, 200);
assert.match(r.headers.get("Content-Disposition"), /zion-pattern-solver-0\.3\.0\.tar\.gz/);
assert.equal(r.headers.get("Content-Type"), "application/gzip");
const tgz = readFileSync(new URL("public/" + DEFAULT_ASSET, here));
assert.equal(tgz[0], 0x1f); assert.equal(tgz[1], 0x8b);

r = await head("/download?asset=zion-pattern-solver-0.3.0.zip");
assert.equal(r.status, 200);
assert.equal(r.headers.get("Content-Type"), "application/zip");

r = await head("/download?asset=zion-pattern-solver-0.2.0.tar.gz");
assert.equal(r.status, 200, "old 0.2.0 link still served (nothing removed)");
console.log("ok download serves 0.3.0: 8 checks");
