#!/usr/bin/env node
// Aggregate dashboard artifacts -> state.json (certificates + security report).
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const REPO = path.resolve(ROOT, "..");

function readJson(p) {
  try {
    return JSON.parse(fs.readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

const certsDir = path.join(REPO, "afreval-harness", "certs");
const certs = fs.existsSync(certsDir)
  ? fs.readdirSync(certsDir).filter((f) => f.endsWith(".cert.json")).map((f) => readJson(path.join(certsDir, f))).filter(Boolean)
  : [];

const security = readJson(path.join(REPO, "afreval-airlock", "attack", "report.json"));

const state = {
  generated_at: new Date().toISOString(),
  certifications: certs.map((c) => ({
    model: c.model,
    context_score: c.score.context_score,
    pass: c.score.pass,
    vectors: c.score.vectors,
    cert_sha256: c.cert_sha256,
  })),
  security,
};

const out = path.join(ROOT, "state.json");
fs.writeFileSync(out, JSON.stringify(state, null, 2));
console.log(`wrote ${out} (${certs.length} certs)`);
