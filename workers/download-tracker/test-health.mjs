// node workers/download-tracker/test-health.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import worker, { DEFAULT_ASSET, gitShaOf } from "./src/index.js";

const pyVersion = readFileSync(new URL("../../pyproject.toml", import.meta.url), "utf8").match(/^version\s*=\s*"([^"]+)"/m)[1];
let puts = 0;
const kv = { get: async () => null, put: async () => { puts++; }, list: async () => ({ keys: [] }) };
async function health(env) {
  const r = await worker.fetch(new Request("https://t.example/v1/health", { headers: { "User-Agent": "Mozilla/5.0" } }), { DOWNLOADS: kv, ...env }, { waitUntil() {} });
  assert.equal(r.status, 200);
  return r.json();
}
const sha = "3236ff612312b657ba7df6b5f12579cae45fd697";
let b = await health({ GIT_SHA: sha });
assert.equal(b.git_sha, sha, "git_sha from GIT_SHA");
assert.equal(b.version, pyVersion, "version tracks pyproject");
assert.equal(b.default_asset, DEFAULT_ASSET);
b = await health({});
assert.equal(b.git_sha, null, "no GIT_SHA -> null, never invented");
for (const bad of ["", "main", "xyz1234", "abc", "a".repeat(41), "3236ff6; rm -rf /"]) assert.equal(gitShaOf({ GIT_SHA: bad }), null, "bad GIT_SHA -> null: " + bad);
assert.equal(gitShaOf({ GIT_SHA: " 3236FF6 " }), "3236ff6");
assert.equal(puts, 0, "health never increments KV");
console.log("ok health exposes git_sha + version: 13 checks");
