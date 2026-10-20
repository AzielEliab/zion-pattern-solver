/**
 * QNS-CD-1.0 mesh cross-map + suite Live Nodes contract.
 *
 * node workers/download-tracker/test-mesh.mjs
 */
import assert from "node:assert/strict";
import {
  MESH_CAVEAT,
  MESH_DEFAULT_OFF,
  MESH_NODE_LIVE,
  MESH_PRESENCE,
  MESH_IDENTITY,
  MESH_NOTE,
  MESH_NODE_GATE,
  MESH_PRODUCT,
  QNM_SPEC,
  QNS_CD,
  QNS_CD_SPEC,
  alignLiveNodes,
  emptyMesh,
  handleMeshApi,
  meshPointer,
  meshStatusLine,
  parseMeshDoc,
  publicMesh,
  withQnsCd,
} from "./src/mesh.js";

assert.equal(QNS_CD_SPEC, "QNS-CD-1.0");
assert.equal(QNS_CD.spec, "QNS-CD-1.0");
assert.equal(QNS_CD.one_line, "photon QNS1 packet transfer");
assert.equal(QNS_CD.softwares_tab, false);
assert.equal(QNS_CD.catalog_product, false);
assert.equal(QNS_CD.public_proxy, false);
assert.equal(QNS_CD.qnsd_proxy, false);
assert.equal(QNS_CD.node_gate, false);
assert.equal(QNS_CD.default_off, false);
assert.equal(QNS_CD.presence, "read-only presence ON; not a live mesh");
assert.equal(QNS_CD.mesh_node_live, false);
assert.equal(QNS_CD.author, "Aziel Eliab");
assert.equal(QNS_CD.identity, "Aziel Eliab");
assert.equal(QNS_CD.local_qnsd.coded_in, "AzielEliab/qnm-node");
assert.equal(QNS_CD.local_qnsd.repo, "https://github.com/AzielEliab/qnm-node");
assert.equal(QNS_CD.local_qnsd.hosted, false);
assert.equal(QNS_CD.runtime.repo, "https://github.com/AzielEliab/aziel-runtime");
assert.equal(QNS_CD.runtime.catalog_field, true);
assert.equal(QNS_CD.pair_custody.product, "azinterface");
assert.match(MESH_NOTE, /QNS-CD-1\.0/);
assert.match(MESH_NOTE, /photon QNS1 packet transfer/);
assert.match(MESH_NOTE, /No public qnsd proxy/);
assert.match(MESH_NOTE, /not a Softwares-tab product/);
assert.equal(MESH_DEFAULT_OFF, false);
assert.equal(MESH_PRESENCE, "read-only presence ON; not a live mesh");
assert.equal(MESH_NODE_LIVE, false);
assert.match(MESH_NOTE, /read-only presence ON; not a live mesh/);
assert.match(MESH_NOTE, /Not a live end-to-end QNM mesh/);
assert.doesNotMatch(MESH_NOTE, /default off/i);
assert.equal(MESH_NODE_GATE, false);
assert.equal(MESH_IDENTITY, "Aziel Eliab");
assert.equal(MESH_PRODUCT, "zsolver");
assert.equal(QNM_SPEC, "QNM-BUILD-1.0");

const empty = emptyMesh();
assert.equal(empty.enabled, false);
assert.equal(empty.default_off, false);
assert.equal(empty.mesh_node_live, false);
assert.equal(empty.presence, MESH_PRESENCE);
assert.equal(empty.node_gate, false);
assert.equal(empty.live_nodes, 0);
assert.equal(empty.qns_cd_spec, QNS_CD_SPEC);
assert.equal(empty.qns_cd.spec, QNS_CD_SPEC);
assert.match(empty.note, /QNS-CD-1\.0/);

const pub = publicMesh(empty);
assert.equal(pub.enabled, false);
assert.equal(pub.qns_cd_spec, QNS_CD_SPEC);
assert.equal(pub.qns_cd.softwares_tab, false);
assert.equal(alignLiveNodes({ mesh: pub }), 0);
assert.match(meshStatusLine(pub), /QNS-CD-1\.0/);

const pointer = meshPointer();
assert.equal(pointer.enabled_default, true);
assert.equal(pointer.mesh_node_live, false);
assert.equal(pointer.qns_cd.qnsd_proxy, false);
assert.match(pointer.note, /QNS-CD-1\.0/);
assert.match(pointer.note, /qnm-node/);

const stamped = withQnsCd({ ok: true, enabled: false, note: "QNM radios/bearers are OFF (default)." });
assert.equal(stamped.enabled, false);
assert.equal(stamped.qns_cd_spec, QNS_CD_SPEC);
assert.match(stamped.note, /QNS-CD-1\.0/);

const onDoc = parseMeshDoc({
  ok: true,
  enabled: true,
  rollup: { live: 2, locked: 1, isolated: 0 },
  nodes: [{ id: "n1", product: "zsolver" }],
});
assert.equal(onDoc.enabled, true);
assert.equal(onDoc.live_nodes, 2);
assert.equal(onDoc.qns_cd_spec, QNS_CD_SPEC);
assert.match(onDoc.note, /QNS-CD-1\.0/);
// When enabled the caveat stays, and the Worker never claims a live mesh node.
assert.match(onDoc.note, /Not a live end-to-end QNM mesh/);
assert.match(onDoc.note, /read-only presence ON; not a live mesh/);
assert.equal(onDoc.mesh_node_live, false);
assert.equal(onDoc.default_off, false);
const onPub = publicMesh(onDoc);
assert.equal(onPub.mesh_node_live, false);
assert.match(meshStatusLine(onPub), /Not a live end-to-end QNM mesh/);
assert.equal(MESH_CAVEAT, "Not a live end-to-end QNM mesh.");
assert.equal(alignLiveNodes({ mesh: onDoc }), 2);

const offUnknown = await handleMeshApi(
  new Request("https://example.test/v1/mesh/not-a-door", { headers: { "user-agent": "Mozilla/5.0" } }),
  new URL("https://example.test/v1/mesh/not-a-door"),
  {},
);
assert.equal(offUnknown.status, 404);
const unknownBody = await offUnknown.json();
assert.equal(unknownBody.code, "MESH-UNKNOWN");
assert.equal(unknownBody.qns_cd_spec, QNS_CD_SPEC);
assert.equal(unknownBody.enabled, false);

// Offline by default: a local AZIEL_RUNTIME binding stands in for the runtime (same shape it serves).
// Set ZPS_LIVE=1 to also check the live runtime over HTTPS.
const LIVE = process.env.ZPS_LIVE === "1";
const fakeRuntime = {
  async fetch(req) {
    const p = new URL(req.url).pathname;
    if (req.method === "POST" && p.endsWith("/enable")) return new Response(JSON.stringify({ ok: false, code: "token_required" }), { status: 401, headers: { "content-type": "application/json" } });
    const body = { ok: true, enabled: true, mesh_default: "on", live_nodes: 0, rollup: { live: 0, locked: 0, isolated: 0 }, nodes: [], note: "read-only presence ON; not a live mesh. Not a live end-to-end QNM mesh." };
    return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
  },
};
for (const env of LIVE ? [{ AZIEL_RUNTIME: fakeRuntime }, { AZIEL_RUNTIME_ORIGIN: "https://aziel-runtime.vibelock.workers.dev" }] : [{ AZIEL_RUNTIME: fakeRuntime }]) {
const status = await handleMeshApi(
  new Request("https://example.test/v1/mesh/status", { headers: { "user-agent": "Mozilla/5.0", accept: "application/json" } }),
  new URL("https://example.test/v1/mesh/status"),
  env,
);
assert.ok(status, "GET /v1/mesh/status should proxy");
assert.equal(status.status, 200, "GET /v1/mesh/status HTTP " + status.status);
const body = await status.json();
// Since 2026-09-12 the suite mesh presents ON by default with no mesh-off kill switch.
// Fail closed: a non-object body, a non-boolean enabled, or any mesh_default other than "on" fails.
assert.ok(body && typeof body === "object" && !Array.isArray(body), "mesh status body must be an object");
assert.equal(body.ok, true, "mesh status must report ok:true");
assert.equal(typeof body.enabled, "boolean", "mesh status enabled must be boolean");
assert.equal(body.mesh_default, "on", "mesh_default must be \"on\"");
assert.equal(body.enabled, true, "mesh must present ON by default");
// Honest counts: no claim of live peers. live_nodes is a count (>= 0), never asserted > 0.
assert.ok(Number.isInteger(body.live_nodes) && body.live_nodes >= 0, "live_nodes must be a non-negative integer count");
assert.equal(alignLiveNodes({ mesh: parseMeshDoc(body) }), body.live_nodes, "Live Nodes pill must equal the reported count, not an invented one");
assert.equal(body.qns_cd_spec, QNS_CD_SPEC);
assert.equal(body.qns_cd.spec, QNS_CD_SPEC);
assert.equal(body.qns_cd.qnsd_proxy, false);
assert.match(String(body.note || ""), /QNS-CD-1\.0/);

const nodes = await handleMeshApi(
  new Request("https://example.test/v1/mesh/nodes", { headers: { "user-agent": "Mozilla/5.0", accept: "application/json" } }),
  new URL("https://example.test/v1/mesh/nodes"),
  env,
);
assert.equal(nodes.status, 200, "GET /v1/mesh/nodes HTTP " + nodes.status);
const nodesBody = await nodes.json();
assert.equal(nodesBody.qns_cd_spec, QNS_CD_SPEC);
assert.equal(nodesBody.qns_cd.softwares_tab, false);

const enable = await handleMeshApi(
  new Request("https://example.test/v1/mesh/enable", {
    method: "POST",
    headers: { "user-agent": "Mozilla/5.0", "content-type": "application/json" },
    body: "{}",
  }),
  new URL("https://example.test/v1/mesh/enable"),
  env,
);
const enableBody = await enable.json();
assert.ok(enable.status >= 400, "empty unauthenticated enable must be refused (HTTP " + enable.status + ")");
assert.notEqual(enableBody.ok, true, "empty enable must not report success");
const parsedLive = parseMeshDoc(body);
assert.equal(parsedLive.mesh_node_live, false, "never claims a live mesh node");
assert.match(parsedLive.note, /Not a live end-to-end QNM mesh/);
}

// Z2: the Worker's own surfaces say presence ON and never "default off".
{
  const { default: worker } = await import("./src/index.js");
  const wenv = { ASSETS: { fetch: async () => new Response("x") }, DOWNLOADS: { get: async () => null, put: async () => {}, list: async () => ({ keys: [] }) } };
  for (const p of ["/", "/openapi.json", "/v1/skill"]) {
    const t = await (await worker.fetch(new Request("https://t.example" + p, { headers: { "User-Agent": "Mozilla/5.0" } }), wenv, { waitUntil() {} })).text();
    assert.ok(t.includes("read-only presence ON; not a live mesh"), p + " says presence ON");
    assert.doesNotMatch(t, /default off|off \(default\)/i, p + " never says default off");
  }
}
console.log("QNS-CD-1.0 cross-map + mesh read-only presence ON, not a live mesh (caveat + mesh_node_live:false) ok" + (LIVE ? " [offline + live]" : " [offline]"));
