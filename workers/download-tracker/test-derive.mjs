/**
 * Worker port of volumes 1–5 derive — keep in lockstep with
 * src/zion_pattern_solver/derive.py
 *
 * node --experimental-vm-modules --test workers/download-tracker/test-derive.mjs
 * (or: node workers/download-tracker/test-derive.mjs)
 */
import assert from "node:assert/strict";
import {
  METHOD,
  capConfidence,
  scoreRequest,
} from "./src/engine.js";

const TITLES = [
  "Marion A. Zioncheck Visual Archive Vol 1 — Primary Documents, Death Certificates & Forensic Analysis",
  "Marion A. Zioncheck Visual Archive Vol 2 — Contemporary News Coverage & Family",
  "Marion A. Zioncheck Visual Archive Vol 3 — Funeral, Personal Photos, Timeline & Research",
  "Marion A. Zioncheck Visual Archive Vol 4 — The Physics Case: Why Marion Zioncheck Could Not Have",
  "Marion A. Zioncheck Vol 5 — The Human & Institutional Evidence",
];

for (const title of TITLES) {
  const scored = scoreRequest({ title });
  const yeses = scored.answers.filter((a) => a.value === "yes");
  assert.equal(scored.seed_corpus, true, title);
  assert.ok(scored.capped_confidence > 0, title);
  assert.ok(scored.capped_confidence <= 0.75, title);
  assert.ok(scored.display > 0, title);
  assert.ok(yeses.length > 0, title);
  assert.equal(scored.method, METHOD);
}

const thin = scoreRequest({
  filename: "Marion_A_Zioncheck_Visual_Archive_Vol_1_Primary_Documents_Death_Certificates_For.pdf",
  subjects: "Marion Zioncheck, investigation",
  keywords: "Zioncheck, evidence, archive",
  domain: "history",
});
assert.equal(thin.seed_corpus, true);
assert.ok(thin.capped_confidence > 0);
assert.ok(thin.answers.some((a) => a.value === "yes"));

const hvac = scoreRequest({
  title: "AEEM HVAC Energy Valve — Consumer Retrofit Whitepaper",
  domain: "engineering",
});
assert.equal(hvac.seed_corpus, false);
assert.equal(hvac.capped_confidence, 0);
assert.equal(hvac.display, 0);

assert.equal(capConfidence(0.99), 0.75);
assert.equal(scoreRequest({ answers: [{ pattern_id: "P1", value: "yes" }] }).derived, false);

console.log("ok worker volumes 1-5 derive");
