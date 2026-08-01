#!/usr/bin/env node
// §3.5 hardening-loop runner: attack program -> validator -> per-seam bypass rate.
// Nightly: node attack/run_attack.js  (exit 1 if any bypass -> CI fails -> promote to regression test)
const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const BIN = path.join(ROOT, "target", "release", "afreval-airlock");
const POLICY = path.join(ROOT, "policies", "demo.json");
const attack = require("./attack_program.js");

const MAX_AGE = 300;

function grant(tool, ageSecs) {
  return execFileSync(BIN, ["grant", "--policy", POLICY, "--tool", tool, "--age-secs", String(ageSecs)]).toString().trim();
}

const toolCalls = [];
const outputPayloads = [];
attack.variants.forEach((v, i) => {
  if (v.kind === "output") {
    outputPayloads.push({ index: i, variant: v });
    return;
  }
  let g = null;
  switch (v.grant) {
    case "valid": g = grant(v.tool, 60); break;
    case "expired": g = grant(v.tool, MAX_AGE + 60); break;
    case "wrongtool": g = grant("send_sms", 60); break;
    case "tampered": g = grant(v.tool, 60) + "x"; break;
    case "wrongkey": g = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b29sIjoidGVzdCIsImlhdCI6MX0.x"; break;
    default: g = null;
  }
  toolCalls.push({ index: i, variant: v, call: { tool: v.tool, arguments: v.args, grant: g } });
});

const verdicts = toolCalls.length
  ? JSON.parse(
      execFileSync(BIN, ["validate", "--policy", POLICY, "--batch"], {
        input: JSON.stringify(toolCalls.map((t) => t.call)),
      }).toString()
    )
  : [];

const bySeam = {};
const bypasses = [];

toolCalls.forEach(({ index, variant }, k) => {
  bySeam[variant.seam] = bySeam[variant.seam] || { total: 0, bypasses: 0 };
  bySeam[variant.seam].total++;
  const v = verdicts[k];
  let bypass = false;
  if (variant.seam === 2) {
    // neutralization semantics: a ghost-arg attack is defended if the injected
    // args were stripped (never reach the tool) OR the call was denied.
    // Allow WITH an empty strip list = the injection survived = bypass.
    bypass = v.decision === "Allow" && v.ghost_args_stripped.length === 0;
  } else {
    bypass = v.decision === "Allow";
  }
  if (bypass) {
    bySeam[variant.seam].bypasses++;
    bypasses.push(`seam ${variant.seam}: ${variant.label}`);
  }
});

outputPayloads.forEach(({ index, variant }) => {
  bySeam[variant.seam] = bySeam[variant.seam] || { total: 0, bypasses: 0 };
  bySeam[variant.seam].total++;
  let ok = true;
  try {
    const masked = execFileSync(BIN, ["sanitize", "--policy", POLICY], { input: variant.payload }).toString();
    const seeds = variant.payload.match(/[\w.+-]+@[\w.-]+|(?:\+?\d[\d\s\-()]{7,}\d)|\d{6,12}/g) || [];
    for (const seed of seeds) {
      if (masked.includes(seed)) {
        ok = false;
        break;
      }
    }
  } catch (e) {
    ok = e.status === 1 ? false : true; // over-cap is blocked, not a bypass
  }
  if (!ok) {
    bySeam[variant.seam].bypasses++;
    bypasses.push(`seam ${variant.seam}: ${variant.label}`);
  }
});

const report = {
  timestamp: new Date().toISOString(),
  total_variants: attack.variants.length,
  total_bypasses: bypasses.length,
  bypasses,
  per_seam: Object.fromEntries(
    Object.entries(bySeam).map(([k, s]) => [k, { total: s.total, bypasses: s.bypasses, rate: Number((s.bypasses / s.total).toFixed(3)) }])
  ),
};

fs.writeFileSync(path.join(__dirname, "report.json"), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
process.exit(bypasses.length ? 1 : 0);
