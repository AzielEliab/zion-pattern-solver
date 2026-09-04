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
  VOLUME_METHOD,
  VOLUME_METHOD_LAYERS,
  applyVolumesMethod,
  capConfidence,
  deriveAnswersFromDocument,
  isZioncheckSeedDocument,
  resolveScorePayload,
  scoreAnswers,
} from "./src/engine.js";

const TITLES = [
  "Marion A. Zioncheck Visual Archive Vol 1 — Primary Documents, Death Certificates & Forensic Analysis",
  "Marion A. Zioncheck Visual Archive Vol 2 — Contemporary News Coverage & Family Battles",
  "Marion A. Zioncheck Visual Archive Vol 3 — Funeral, Personal Photos, Timeline & Research",
  "Marion A. Zioncheck Visual Archive Vol 4 — The Physics Case: Why Marion Zioncheck Could Not Have Jumped",
  "Marion A. Zioncheck Vol 5 — The Human & Institutional Evidence",
];

for (const title of TITLES) {
  const scored = resolveScorePayload({ title });
  const yeses = scored.answers.filter((a) => a.value === "yes");
  assert.equal(scored.seed_corpus, true, title);
  assert.equal(scored.capped_confidence, 0.75, title);
  assert.equal(scored.display, 75, title);
  assert.ok(yeses.length > 0, title);
  assert.equal(scored.method, VOLUME_METHOD);
  assert.equal(scored.method, METHOD);
}
assert.deepEqual(Object.keys(VOLUME_METHOD_LAYERS).map(Number), [1, 2, 3, 4, 5]);
assert.deepEqual(VOLUME_METHOD_LAYERS[1].layers, ["seed_patterns"]);
assert.deepEqual(VOLUME_METHOD_LAYERS[2].layers, [
  "pattern_of_official_story_to_silence",
  "pattern_of_suppression",
]);
assert.deepEqual(VOLUME_METHOD_LAYERS[3].layers, ["pattern_questions"]);
assert.deepEqual(VOLUME_METHOD_LAYERS[4].layers, [
  "seed_patterns",
  "pattern_of_official_story_to_silence",
]);
assert.deepEqual(VOLUME_METHOD_LAYERS[5].layers, ["pattern_of_suppression"]);
assert.ok(VOLUME_METHOD_LAYERS[2].public_title.includes("Family Battles"));
assert.ok(VOLUME_METHOD_LAYERS[4].public_title.includes("Jumped"));
assert.equal(deriveAnswersFromDocument({ title: TITLES[0] }).seed_corpus, true);

const thin = resolveScorePayload({
  filename: "Marion_A_Zioncheck_Visual_Archive_Vol_1_Primary_Documents_Death_Certificates_For.pdf",
  subjects: "Marion Zioncheck, investigation",
  keywords: "Zioncheck, evidence, archive",
  domain: "history",
});
assert.equal(thin.seed_corpus, true);
assert.equal(thin.capped_confidence, 0.75);
assert.equal(thin.display, 75);
assert.ok(thin.answers.some((a) => a.value === "yes"));

const hvac = resolveScorePayload({
  title: "AEEM HVAC Energy Valve — Consumer Retrofit Whitepaper",
  domain: "engineering",
});
assert.equal(hvac.seed_corpus, false);
assert.equal(hvac.capped_confidence, 0);
assert.equal(hvac.display, 0);

assert.equal(capConfidence(0.99), 0.75);
assert.equal(resolveScorePayload({ answers: [{ pattern_id: "P1", value: "yes" }] }).derived, false);
const lone = resolveScorePayload({ answers: [{ pattern_id: "P1", value: "yes" }] });
assert.ok(lone.display < 75, "P1-only is natural-occurrence, not intentional 75");
assert.ok(Math.abs(lone.raw_confidence - 0.35) < 1e-9);

const arctic = resolveScorePayload({
  title: "Arctic Building event window, Seattle, 7 August 1936",
});
assert.equal(arctic.seed_corpus, false);
assert.notEqual(arctic.display, 75);

assert.equal(isZioncheckSeedDocument("marion zioncheck newspaper clipping"), false);
assert.equal(isZioncheckSeedDocument("arctic building event window"), false);
assert.equal(isZioncheckSeedDocument("marion a zioncheck visual archive vol 2"), true);
const vol1layers = applyVolumesMethod("marion a zioncheck visual archive vol 1 primary documents");
assert.equal(vol1layers.seed_corpus, true);
assert.ok(vol1layers.layers.includes("seed_patterns"));
assert.ok(vol1layers.layers.length < 5, "do not stuff all five layers on one volume");

const sparse = resolveScorePayload({ title: "Death certificate inventory note", domain: "records" });
const weak = resolveScorePayload({
  title: "Window geometry field memo",
  body: "sill height and building access last confirmed",
});
const strong = resolveScorePayload({
  title: "Official narrative lock and institutional suppression file",
  body:
    "timeline research funeral personal photos witness question evidence archive finding aid custody stationery investigation coroner suppression discredit unfit psychiatric congressional news coverage family battles official suicide jumped could not have wire narrative lock physics case official account official story",
});
assert.equal(sparse.seed_corpus, false);
assert.equal(weak.seed_corpus, false);
assert.equal(strong.seed_corpus, false);
assert.ok(sparse.display >= 1 && sparse.display < 75);
assert.ok(weak.display >= 1 && weak.display < 75);
assert.ok(strong.display >= 1 && strong.display <= 75);
assert.ok(strong.display > sparse.display);
assert.ok(strong.display > weak.display);
assert.ok(new Set([sparse.display, weak.display, strong.display]).size >= 2);

const oneYes = scoreAnswers([
  { pattern_id: "P1", value: "yes" },
  { pattern_id: "P2", value: "unknown" },
  { pattern_id: "P3", value: "unknown" },
  { pattern_id: "P4", value: "unknown" },
  { pattern_id: "P5", value: "unknown" },
  { pattern_id: "P6", value: "unknown" },
  { pattern_id: "P7", value: "unknown" },
  { pattern_id: "P8", value: "unknown" },
  { pattern_id: "P9", value: "unknown" },
]);
assert.ok(oneYes.raw_confidence < 0.4, "unknowns must pull the denominator");

console.log("ok worker volumes 1-5 derive");
