/**
 * QNS-CD-1.0 mesh cross-map + suite Live Nodes contract.
 *
 * node workers/download-tracker/test-mesh.mjs
 */
import assert from "node:assert/strict";
import {
  MESH_DEFAULT_OFF,
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
assert.equal(QNS_CD.default_off, true);
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
assert.equal(MESH_DEFAULT_OFF, true);
assert.equal(MESH_NODE_GATE, false);
assert.equal(MESH_IDENTITY, "Aziel Eliab");
assert.equal(MESH_PRODUCT, "zsolver");
assert.equal(QNM_SPEC, "QNM-BUILD-1.0");

const empty = emptyMesh();
assert.equal(empty.enabled, false);
assert.equal(empty.default_off, true);
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
assert.equal(pointer.enabled_default, false);
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

const env = { AZIEL_RUNTIME_ORIGIN: "https://aziel-runtime.vibelock.workers.dev" };
const status = await handleMeshApi(
  new Request("https://example.test/v1/mesh/status", { headers: { "user-agent": "Mozilla/5.0", accept: "application/json" } }),
  new URL("https://example.test/v1/mesh/status"),
  env,
);
assert.ok(status, "GET /v1/mesh/status should proxy");
assert.equal(status.status, 200, "GET /v1/mesh/status HTTP " + status.status);
const body = await status.json();
assert.equal(body.enabled, false, "mesh must stay default OFF");
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
assert.equal(enableBody.enabled === true, false, "empty enable must not turn mesh on");

console.log("QNS-CD-1.0 cross-map + mesh default OFF ok");
