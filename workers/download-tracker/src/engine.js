/**
 * ZionPattern Solver runtime (Worker port).
 *
 * Provisional and assistive only. Does not solve Zioncheck or any case.
 * Hard cap: displayed/stored conclusion confidence never exceeds 0.75.
 * Irreducible uncertainty floor: 25%.
 */
export const CONFIDENCE_CAP = 0.75;
export const UNCERTAINTY_FLOOR = 0.25;
export const SCHEMA_VERSION = "0.2.0";
export const DISCLAIMER =
  "Provisional and assistive only. Does not solve Zioncheck or any case. Hard cap 75% / uncertainty floor 25%.";

const PRIORITY_WEIGHT = { critical: 1.0, high: 0.7, medium: 0.4 };

export const PATTERNS = [
  {
    id: "P1",
    name: "Kinematic & Timeline Impossibility",
    priority: "critical",
    core_contradiction:
      "The published August 7, 1936 timeline cannot simultaneously satisfy last-confirmed public movements, building access, and the reported event window without an unexplained gap.",
    question_templates: [
      { prompt: "Does the published August 7, 1936 timeline leave an unexplained gap between the last confirmed public sighting of Representative Marion A. Zioncheck and the Arctic Building event window?", evidence_type: "timeline" },
      { prompt: "Do contemporaneous public accounts disagree on the clock time and sequence of movements inside or toward the Arctic Building?", evidence_type: "timeline" },
      { prompt: "Is the official kinematic account (window geometry, approach, and elapsed time) under-specified in surviving public reports such that it cannot be independently reconstructed?", evidence_type: "forensic" },
    ],
    detection_heuristic: "Flag when two or more public clocks or routes cannot be true at once, or when reconstruction requires unstated intervals.",
    evidence_priority: "timeline tables, building plans, contemporaneous press clocks",
    version: SCHEMA_VERSION,
  },
  {
    id: "P2",
    name: "Document Provenance & Integrity",
    priority: "critical",
    core_contradiction:
      "Publicly catalogued stationery and note artifacts tied to the 1936 record raise provenance and physical-integrity questions (emboss, transport, overwrite) that the official account does not resolve.",
    question_templates: [
      { prompt: "Do public archival catalogs describe the purported 1936 note as written on U.S. House stationery whose custody chain is incomplete?", evidence_type: "document" },
      { prompt: "Have independent catalogs or later inventories noted physical anomalies (off-center emboss, transport creases, erasure or overwrite marks) on documents associated with the 1936 record?", evidence_type: "document" },
      { prompt: "Is there a published finding aid that cannot place the note's creation time relative to the Arctic Building event window?", evidence_type: "document" },
    ],
    detection_heuristic: "Flag stationery/note items whose catalog entries mention incomplete custody, later insertion, or physical alteration indicators.",
    evidence_priority: "finding aids, stationery photographs, custody logs",
    version: SCHEMA_VERSION,
  },
  {
    id: "P3",
    name: "Witness & Archival Void",
    priority: "high",
    core_contradiction:
      "Named contemporaneous witnesses and expected institutional records are missing, delayed, unnamed, or compressed in the public archive.",
    question_templates: [
      { prompt: "Does the public archive lack named, on-the-record witnesses for the minutes surrounding the Arctic Building event, beyond later second-hand summaries?", evidence_type: "witness" },
      { prompt: "Are expected institutional files (building, police blotter, coroner docket) absent, delayed, or reduced to a short summary in surviving catalogs?", evidence_type: "archive" },
      { prompt: "Do later retellings introduce an unnamed or late-appearing figure whose role is not anchored in a contemporaneous named source?", evidence_type: "witness" },
    ],
    detection_heuristic: "Flag unnamed 'someone' figures, missing blotters, and summaries that replace primary witness lists.",
    evidence_priority: "blotters, named depositions, building logs, catalog gaps",
    version: SCHEMA_VERSION,
  },
  {
    id: "P4",
    name: "Geographic / Location Manipulation",
    priority: "medium",
    core_contradiction:
      "Public location claims — Arctic Building, travel between Washington, D.C. and Seattle, and reported routes — contain inconsistencies in the surviving 1936 record.",
    question_templates: [
      { prompt: "Do public sources disagree on which Arctic Building floor, window, or street-facing elevation is described?", evidence_type: "geographic" },
      { prompt: "Is the D.C.–Seattle travel itinerary in the days before August 7, 1936 internally inconsistent across public schedules?", evidence_type: "timeline" },
      { prompt: "Do maps or building directories from 1936 fail to corroborate a location detail that later narratives treat as settled?", evidence_type: "geographic" },
    ],
    detection_heuristic: "Flag floor/window/route mismatches and itineraries that skip required travel time.",
    evidence_priority: "1936 directories, rail/air schedules, building plans",
    version: SCHEMA_VERSION,
  },
  {
    id: "P5",
    name: "Pre-Event Discrediting & Suppression",
    priority: "high",
    core_contradiction:
      "In the months before August 1936, public and Congressional framing shifted toward incapacity and psychiatric narratives in ways that later constrained what questions could be asked.",
    question_templates: [
      { prompt: "Does the Congressional Record or contemporaneous press show a pre-August 1936 shift toward depicting Zioncheck as unfit, before the Arctic Building event?", evidence_type: "media" },
      { prompt: "Are there public expungement, omission, or 'not printed' notes in the Congressional Record around Zioncheck's 1936 speeches?", evidence_type: "document" },
      { prompt: "Did official or press psychiatric framing precede independent examination of the 1936 scene in published accounts?", evidence_type: "media" },
    ],
    detection_heuristic: "Flag incapacity narratives that lock in before scene measurements or named forensic files exist.",
    evidence_priority: "Congressional Record, 1936 press, hospital-admission public notices",
    version: SCHEMA_VERSION,
  },
  {
    id: "P6",
    name: "Political / Motive Contextual",
    priority: "medium",
    core_contradiction:
      "Zioncheck's public political conflicts (New Deal left, anti-war positions, Washington state machine fights) supply motive-context that a suicide-only official account does not engage. Context is not proof.",
    question_templates: [
      { prompt: "Does the official public account engage Zioncheck's documented 1935–1936 political conflicts as investigative context, or does it omit them?", evidence_type: "political" },
      { prompt: "Are there contemporaneous public threats, expulsions-from-floor episodes, or machine-politics clashes recorded in newspapers or the Record that later summaries drop?", evidence_type: "political" },
      { prompt: "Would an analyst relying only on the official one-line cause miss publicly documented political context from 1936?", evidence_type: "political" },
    ],
    detection_heuristic: "Flag official summaries that strip documented political conflict and leave only a medical/suicide line.",
    evidence_priority: "1936 newspapers, Congressional Record, campaign files",
    version: SCHEMA_VERSION,
  },
  {
    id: "P7",
    name: "Secondary Encoded Testimony / Rubye",
    priority: "critical",
    core_contradiction:
      "Later public artistic and documentary work associated with Rubye (widow of Marion A. Zioncheck) is treated by some researchers as encoded testimony. This is a pattern to interrogate, not a conclusion and not an accusation of any living person.",
    question_templates: [
      { prompt: "Does publicly exhibited or published work associated with Rubye after 1936 use dates, architecture, or documentary fragments that point back to the August 1936 record?", evidence_type: "artistic" },
      { prompt: "Have catalogs of that work noted geometric or archival markers that independent researchers have proposed as testimony rather than solely as memorial art?", evidence_type: "artistic" },
      { prompt: "Is there a citable public source (exhibition note, memoir, dated artwork) rather than rumor for any Rubye-linked claim used in this session?", evidence_type: "document" },
    ],
    detection_heuristic: "Require a citable public artifact. Treat interpretation as provisional; never treat art as a verdict.",
    evidence_priority: "exhibition catalogs, dated public artworks, memoirs",
    version: SCHEMA_VERSION,
  },
  {
    id: "P8",
    name: "Rapid Narrative Lock",
    priority: "high",
    core_contradiction:
      "Press and official statements locked a suicide narrative within hours, before independent measurement of the scene appears in the public record.",
    question_templates: [
      { prompt: "Did major Seattle or wire-service accounts on August 7–8, 1936 state a suicide conclusion before naming an independent examiner or publishing scene measurements?", evidence_type: "media" },
      { prompt: "Do later editions copy the first-day cause line with no added forensic detail?", evidence_type: "media" },
      { prompt: "Is there a public correction, reopen, or dissenting official note in 1936 that failed to move the locked narrative?", evidence_type: "media" },
    ],
    detection_heuristic: "Flag same-day cause-of-death lock plus copy-forward across editions.",
    evidence_priority: "edition timestamps, wire copy, official bulletins",
    version: SCHEMA_VERSION,
  },
  {
    id: "P9",
    name: "Forensic / Physical Evidence Gap",
    priority: "high",
    core_contradiction:
      "No surviving independent forensic file (scene measurements, window geometry, medical-examiner chain of custody) is adequate to test the official kinematic claim.",
    question_templates: [
      { prompt: "Does a public catalog list a 1936 medical-examiner or coroner file with measurements that would let an independent analyst test the official account?", evidence_type: "forensic" },
      { prompt: "Are window dimensions, sill height, and interior layout of the relevant Arctic Building room present in a 1936 or later survey usable as evidence?", evidence_type: "forensic" },
      { prompt: "Is the chain of custody for physical items (clothing, note, photographs) documented in a public finding aid?", evidence_type: "forensic" },
    ],
    detection_heuristic: "Flag missing measurements, missing examiner name, or custody that jumps from scene to narrative.",
    evidence_priority: "coroner dockets, building surveys, photo logs",
    version: SCHEMA_VERSION,
  },
];

const PRIORITY_OF = Object.fromEntries(PATTERNS.map((p) => [p.id, p.priority]));

export const VOLUME_METHOD =
  "seed_patterns×pattern_answers×pattern_questions×pattern_of_suppression×pattern_of_official_story_to_silence";
export const METHOD = VOLUME_METHOD;
export const PRODUCT_VERSION = "0.3.0";

const LAYER_SEED = "seed_patterns";
const LAYER_ANSWERS = "pattern_answers";
const LAYER_QUESTIONS = "pattern_questions";
const LAYER_SUPPRESSION = "pattern_of_suppression";
const LAYER_SILENCE = "pattern_of_official_story_to_silence";
const ALL_LAYERS = [LAYER_SEED, LAYER_ANSWERS, LAYER_QUESTIONS, LAYER_SUPPRESSION, LAYER_SILENCE];

const PATTERN_LAYERS = {
  P1: [LAYER_SEED, LAYER_QUESTIONS, LAYER_SILENCE],
  P2: [LAYER_SEED, LAYER_ANSWERS],
  P3: [LAYER_ANSWERS, LAYER_QUESTIONS, LAYER_SUPPRESSION],
  P4: [LAYER_SEED],
  P5: [LAYER_SUPPRESSION, LAYER_SILENCE],
  P6: [LAYER_SUPPRESSION, LAYER_SILENCE],
  P7: [LAYER_QUESTIONS],
  P8: [LAYER_SUPPRESSION, LAYER_SILENCE],
  P9: [LAYER_SEED, LAYER_ANSWERS, LAYER_SILENCE],
};

const DOCUMENT_FIELDS = ["title", "body", "text", "filename", "subjects", "keywords", "domain"];

const SEED_MARKERS = [
  "zioncheck",
  "marion a zioncheck",
  "marion zioncheck",
  "arctic building",
  "azielcorpuslibrary",
];

export const VOLUME_METHOD_LAYERS = {
  1: {
    public_title: "Primary Documents, Death Certificates & Forensic Analysis",
    layers: [LAYER_SEED],
    role: "seed patterns (+ forensic evidence)",
    signals: ["primary documents", "death certificate", "death certificates", "forensic analysis", "forensic"],
  },
  2: {
    public_title: "Contemporary News Coverage & Family Battles",
    layers: [LAYER_SILENCE, LAYER_SUPPRESSION],
    role: "official story to silence + suppression",
    signals: ["contemporary news", "news coverage", "family battles", "family"],
  },
  3: {
    public_title: "Funeral, Personal Photos, Timeline & Research",
    layers: [LAYER_QUESTIONS],
    role: "pattern questions",
    signals: ["funeral", "personal photos", "timeline", "research"],
  },
  4: {
    public_title: "The Physics Case: Why Marion Zioncheck Could Not Have Jumped",
    layers: [LAYER_SEED, LAYER_SILENCE],
    role: "seed kinematic contradiction of official story",
    signals: ["physics case", "could not have", "could not have jumped", "kinematic"],
  },
  5: {
    public_title: "The Human & Institutional Evidence",
    layers: [LAYER_SUPPRESSION],
    role: "suppression / institutional void",
    signals: ["human & institutional", "human and institutional", "institutional evidence", "institutional void", "institutional"],
  },
};

const ONTOLOGY_LAYER_SIGNALS = {
  [LAYER_SEED]: ["august 7", "1936", "window geometry", "event window", "last confirmed", "building access"],
  [LAYER_ANSWERS]: [
    "evidence",
    "archive",
    "finding aid",
    "custody",
    "stationery",
    "investigation",
    "death certificate",
    "coroner",
    "primary document",
  ],
  [LAYER_QUESTIONS]: [
    "timeline",
    "research",
    "funeral",
    "personal photos",
    "rubye",
    "encoded testimony",
    "witness",
    "question",
  ],
  [LAYER_SUPPRESSION]: [
    "suppression",
    "discredit",
    "unfit",
    "psychiatric",
    "expungement",
    "not printed",
    "congressional",
    "news coverage",
    "institutional",
    "family battles",
  ],
  [LAYER_SILENCE]: [
    "official",
    "suicide",
    "jumped",
    "could not have",
    "wire",
    "narrative lock",
    "one-line",
    "physics case",
    "official account",
    "official story",
  ],
};

const QUESTION_FRAGMENTS = [
  "unexplained gap",
  "house stationery",
  "named, on-the-record",
  "street-facing elevation",
  "depicting zioncheck as unfit",
  "political conflicts",
  "work associated with rubye",
  "suicide conclusion",
  "medical-examiner or coroner",
];

function flattenField(value) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(flattenField).join(" ");
  if (typeof value === "object") return Object.values(value).map(flattenField).join(" ");
  return String(value);
}

export function haystackFrom(document) {
  if (!document || typeof document !== "object") return "";
  const parts = DOCUMENT_FIELDS.filter((k) => document[k] != null).map((k) => flattenField(document[k]));
  const raw = parts.join(" ");
  return raw.replace(/[_\-.]/g, " ").toLowerCase().replace(/\s+/g, " ").trim();
}

export function hasDocumentFields(payload) {
  if (!payload || typeof payload !== "object") return false;
  return DOCUMENT_FIELDS.some((key) => {
    const value = payload[key];
    if (value == null) return false;
    if (typeof value === "string") return value.trim() !== "";
    if (Array.isArray(value)) return value.length > 0;
    return true;
  });
}

export function looksLikeAnswers(raw) {
  if (raw == null) return false;
  if (Array.isArray(raw)) {
    if (!raw.length) return false;
    return raw.some((item) => {
      if (typeof item === "string") {
        const token = item.trim().toLowerCase();
        return token.startsWith("p") || token === "yes" || token === "no" || token === "unknown";
      }
      if (item && typeof item === "object") {
        const value = String(item.value || item.answer || item.v || "").toLowerCase();
        return value === "yes" || value === "no" || value === "unknown" || item.pattern_id || item.qid;
      }
      return false;
    });
  }
  if (typeof raw === "object") {
    return Object.entries(raw).some(([key, value]) => {
      if (/^p[1-9](:q\d+)?$/i.test(key)) return true;
      const inner = value && typeof value === "object" ? value.value || value.answer : value;
      const s = String(inner || "").toLowerCase();
      return s === "yes" || s === "no" || s === "unknown";
    });
  }
  return false;
}

export function isSeedCorpus(text) {
  if (!text) return false;
  if (SEED_MARKERS.some((marker) => text.includes(marker))) return true;
  if (text.includes("marion") && text.includes("zioncheck")) return true;
  if (text.includes("arctic") && text.includes("building")) return true;
  return false;
}

export function matchVolumes(text) {
  const seedish = isSeedCorpus(text);
  const matched = [];
  for (const [key, vol] of Object.entries(VOLUME_METHOD_LAYERS)) {
    const n = Number(key);
    const numbered = text.includes(`vol ${n}`) || text.includes(`volume ${n}`) || text.includes(`vol${n}`);
    const titled = Boolean(vol.public_title) && text.includes(vol.public_title.toLowerCase());
    const signaled = vol.signals.some((signal) => text.includes(signal));
    if (numbered || titled || (signaled && seedish)) matched.push(n);
  }
  return matched;
}

function layersFromOntology(text) {
  const active = new Set();
  if (!text) return active;
  for (const [layer, signals] of Object.entries(ONTOLOGY_LAYER_SIGNALS)) {
    if (signals.some((sig) => text.includes(sig))) active.add(layer);
  }
  let hits = 0;
  for (const frag of QUESTION_FRAGMENTS) {
    if (text.includes(frag)) hits += 1;
  }
  if (hits) {
    active.add(LAYER_QUESTIONS);
    active.add(LAYER_ANSWERS);
  }
  return active;
}

export function activeLayers(text, seed = null) {
  const isSeed = seed == null ? isSeedCorpus(text) : Boolean(seed);
  const layers = new Set();
  const volumes = matchVolumes(text);
  if (isSeed) ALL_LAYERS.forEach((layer) => layers.add(layer));
  for (const [key, vol] of Object.entries(VOLUME_METHOD_LAYERS)) {
    if (volumes.includes(Number(key))) vol.layers.forEach((layer) => layers.add(layer));
  }
  if (isSeed || volumes.length) {
    layersFromOntology(text).forEach((layer) => layers.add(layer));
    if ([LAYER_SEED, LAYER_QUESTIONS, LAYER_SUPPRESSION, LAYER_SILENCE].some((layer) => layers.has(layer))) {
      layers.add(LAYER_ANSWERS);
    }
  }
  return ALL_LAYERS.filter((layer) => layers.has(layer));
}

export function deriveAnswersFromDocument(document) {
  const text = haystackFrom(document);
  const seed = isSeedCorpus(text);
  const layers = activeLayers(text, seed);
  const layerSet = new Set(layers);
  const volumes = matchVolumes(text);
  const answers = PATTERNS.map((pat) => {
    const drivers = PATTERN_LAYERS[pat.id] || [];
    const fired = drivers.filter((layer) => layerSet.has(layer));
    if (fired.length) {
      return {
        pattern_id: pat.id,
        value: "yes",
        qid: "",
        rationale: `volumes-method:${fired.join("×")}`,
      };
    }
    return {
      pattern_id: pat.id,
      value: "unknown",
      qid: "",
      rationale: pat.id === "P7" && !seed ? "require-miss" : "",
    };
  });
  return {
    answers,
    seed_corpus: seed,
    method: layers.length ? VOLUME_METHOD : null,
    layers_active: layers.length ? layers : null,
    volumes_matched: volumes,
    derived: true,
  };
}

export function iterQuestions() {
  const out = [];
  for (const pat of PATTERNS) {
    pat.question_templates.forEach((tmpl, i) => {
      out.push({
        qid: `${pat.id}:q${i}`,
        pattern_id: pat.id,
        index: i,
        prompt: tmpl.prompt,
        evidence_type: tmpl.evidence_type,
        pattern_name: pat.name,
        priority: pat.priority,
      });
    });
  }
  return out;
}

export function capConfidence(raw) {
  const value = Number(raw);
  if (!Number.isFinite(value) || value < 0) return 0.0;
  return Math.min(value, CONFIDENCE_CAP);
}

function unit(value, high = 1.0) {
  const v = Number(value);
  if (!Number.isFinite(v) || v < 0) return 0.0;
  return Math.min(v, high);
}

export function emptyScores() {
  return {
    official_contradiction: 0,
    alternative_coherence: 0,
    raw_confidence: 0,
    capped_confidence: 0,
  };
}

function normalizeAnswers(raw) {
  if (raw == null) return [];
  if (Array.isArray(raw)) {
    return raw.map((a) => {
      if (typeof a === "string") {
        const parts = a.split(/[:\s]+/);
        return { pattern_id: parts[0], value: parts[1] || "unknown", qid: a };
      }
      const qid = a.qid || a.id || "";
      let pid = a.pattern_id || a.pattern || "";
      if (!pid && typeof qid === "string" && qid.includes(":")) pid = qid.split(":")[0];
      return {
        pattern_id: String(pid),
        value: String(a.value || a.answer || a.v || "unknown").toLowerCase(),
        qid: String(qid || ""),
        rationale: a.rationale || "",
      };
    });
  }
  if (typeof raw === "object") {
    return Object.entries(raw).map(([k, v]) => {
      const qid = k;
      const pid = k.includes(":") ? k.split(":")[0] : k;
      const value = typeof v === "object" && v ? v.value || v.answer : v;
      return {
        pattern_id: pid,
        value: String(value || "unknown").toLowerCase(),
        qid,
        rationale: typeof v === "object" && v ? v.rationale || "" : "",
      };
    });
  }
  return [];
}

export function scoreAnswers(rawAnswers) {
  const answers = normalizeAnswers(rawAnswers);
  let ocNum = 0, ocDen = 0, acNum = 0, acDen = 0;
  let unknowns = 0;
  for (const ans of answers) {
    const value = String(ans.value || "unknown").toLowerCase();
    const priority = String(PRIORITY_OF[ans.pattern_id] || "medium").toLowerCase();
    const w = Number(PRIORITY_WEIGHT[priority] ?? 0.4);
    const crit = priority === "critical" ? 1.35 : 1.0;
    if (value === "yes") {
      ocNum += w;
      ocDen += w;
      acNum += w * crit;
      acDen += w * crit;
    } else if (value === "no") {
      ocDen += w;
      acDen += w * crit;
    } else {
      unknowns += 1;
    }
  }
  const oc = ocDen ? ocNum / ocDen : 0.0;
  const ac = acDen ? acNum / acDen : 0.0;
  const raw = 0.55 * oc + 0.45 * ac;
  const capped = capConfidence(raw);
  const uncertainty = capped ? Math.max(UNCERTAINTY_FLOOR, 1 - capped) : 1.0;
  return {
    official_contradiction: unit(oc),
    alternative_coherence: unit(ac),
    raw_confidence: unit(raw, 1.0),
    capped_confidence: capped,
    uncertainty,
    unknown_answers: unknowns,
    answered: answers.length,
    answers,
  };
}

export function deriveAnswers(document) {
  return deriveAnswersFromDocument(document);
}

export function resolveScorePayload(body) {
  const src = body && typeof body === "object" ? body : {};
  let derivation = null;
  let rawAnswers = src.answers != null ? src.answers : src;
  if (looksLikeAnswers(src.answers)) {
    rawAnswers = src.answers;
  } else if (hasDocumentFields(src) || isSeedCorpus(haystackFrom(src))) {
    derivation = deriveAnswersFromDocument(src);
    rawAnswers = derivation.answers;
  } else if (looksLikeAnswers(src)) {
    rawAnswers = src;
  } else if (src && (hasDocumentFields(src) || Object.keys(src).length)) {
    derivation = deriveAnswersFromDocument(src);
    rawAnswers = derivation.answers;
  }
  const scored = scoreAnswers(rawAnswers);
  const out = {
    official_contradiction: scored.official_contradiction,
    alternative_coherence: scored.alternative_coherence,
    raw_confidence: scored.raw_confidence,
    capped_confidence: scored.capped_confidence,
    uncertainty: scored.uncertainty,
    confidence_cap: CONFIDENCE_CAP,
    uncertainty_floor: UNCERTAINTY_FLOOR,
    answered: scored.answered,
    unknown_answers: scored.unknown_answers,
    answers: scored.answers,
    display: Math.round(scored.capped_confidence * 100),
    derived: Boolean(derivation),
    seed_corpus: Boolean(derivation && derivation.seed_corpus),
    method: derivation ? derivation.method : null,
    layers_active: derivation ? derivation.layers_active : null,
    disclaimer: DISCLAIMER,
  };
  if (derivation && derivation.volumes_matched) out.volumes_matched = derivation.volumes_matched;
  return out;
}

export function scoreRequest(body) {
  return resolveScorePayload(body);
}

export function sessionSnapshot(body) {
  const caseName = (body && (body.case || body.case_id)) || "untitled";
  const resolved = scoreRequest(body && typeof body === "object" ? body : {});
  const scores = resolved;
  const questions = iterQuestions();
  const answeredIds = new Set(scores.answers.map((a) => a.qid).filter(Boolean));
  const remaining = questions.filter((q) => !answeredIds.has(q.qid));
  return {
    case: caseName,
    question: remaining[0] || null,
    remaining: remaining.length,
    answered: scores.answered,
    scores: {
      official_contradiction: round6(scores.official_contradiction),
      alternative_coherence: round6(scores.alternative_coherence),
      raw_confidence: round6(scores.raw_confidence),
      capped_confidence: round6(scores.capped_confidence),
    },
    capped_confidence: round6(scores.capped_confidence),
    confidence_cap: CONFIDENCE_CAP,
    uncertainty_floor: UNCERTAINTY_FLOOR,
    uncertainty: round6(scores.uncertainty),
    history: scores.answers,
    patterns: PATTERNS,
    disclaimer: DISCLAIMER,
    note: "Does not solve cases. Human-in-the-loop. Receipts belong on the local Python engine.",
  };
}

function round6(n) {
  return Math.round(n * 1e6) / 1e6;
}

export function patternsPayload() {
  return {
    version: SCHEMA_VERSION,
    product_version: PRODUCT_VERSION,
    confidence_cap: CONFIDENCE_CAP,
    uncertainty_floor: UNCERTAINTY_FLOOR,
    disclaimer: DISCLAIMER,
    method: VOLUME_METHOD,
    volume_method_layers: VOLUME_METHOD_LAYERS,
    author: "Aziel Eliab",
    patterns: PATTERNS,
    questions: iterQuestions(),
  };
}
