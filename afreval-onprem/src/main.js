const { invoke } = window.__TAURI__.core;

const REPORT_SAMPLE = {
  model_id: "example-model",
  harness: { afri_fertility_pin: "0.1.0", afrobench_lite_pin: "f4d4b3de", waxal_pin: "pending" },
  linguistic_fidelity: { waxal_macro_wer: 0.38, afrobench_lite_accuracy: 0.62 },
  cultural_safety: { bias_corrected_judge_score: 78.0 },
  structural_economics: { mean_fertility_premium: 2.68 },
};

const WEIGHTS_SAMPLE = `vertical: telco
version: 1
weights:
  linguistic_fidelity: 0.50
  cultural_safety: 0.20
  structural_economics: 0.30
linguistic_fidelity_internal:
  acoustic: 0.60
  textual: 0.40
threshold: 70.0
`;

async function score() {
  const report = document.querySelector("#report").value;
  const weights = document.querySelector("#weights").value;
  const out = document.querySelector("#out");
  try {
    out.textContent = await invoke("score_report", { reportJson: report, weightsYaml: weights });
  } catch (e) {
    out.textContent = "error: " + e;
  }
}

async function validate() {
  const call = document.querySelector("#call").value;
  const policy = document.querySelector("#policy").value;
  const out = document.querySelector("#out2");
  try {
    out.textContent = await invoke("validate_tool_call", { callJson: call, policyJson: policy });
  } catch (e) {
    out.textContent = "error: " + e;
  }
}

async function status() {
  const out = document.querySelector("#out3");
  out.textContent = await invoke("clearance_status");
}

async function grant() {
  const out = document.querySelector("#out5");
  const tool = document.querySelector("#grant-tool").value;
  try {
    out.textContent = await invoke("sign_grant", { tool });
  } catch (e) {
    out.textContent = "error: " + e;
  }
}

async function security() {
  const out = document.querySelector("#out4");
  try {
    const raw = await invoke("security_report");
    const r = JSON.parse(raw);
    let lines = [
      `run: ${r.timestamp}`,
      `total variants: ${r.total_variants}`,
      `bypasses: ${r.total_bypasses}`,
      "per-seam bypass rate (never aggregate):",
    ];
    for (const [seam, s] of Object.entries(r.per_seam)) {
      lines.push(`  seam ${seam}: ${s.bypasses}/${s.total} (${(s.rate * 100).toFixed(1)}%)`);
    }
    if (r.bypasses.length) {
      lines.push("bypasses:");
      r.bypasses.forEach((b) => lines.push("  " + b));
    }
    out.textContent = lines.join("\n");
  } catch (e) {
    out.textContent = "error: " + e;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  document.querySelector("#report").value = JSON.stringify(REPORT_SAMPLE, null, 2);
  document.querySelector("#weights").value = WEIGHTS_SAMPLE;
  document.querySelector("#policy").value = JSON.stringify(
    {
      allowed_tools: ["query_customer", "get_balance", "send_sms"],
      schemas: {
        query_customer: { params: { customer_id: { type: "string", required: true } } },
        get_balance: { params: { account: { type: "string", required: true } } },
        send_sms: { params: { to: { type: "string", required: true }, message: { type: "string", required: true } } },
      },
      output_max_bytes: 8192,
      clearance: { hmac_key_b64: "CNXxf4RhmTbsqtWMnzgPxnLARJB3Hw-zpudJpIiwxXk", max_age_secs: 300 },
      reauth_tools: ["send_sms", "get_balance"],
    },
    null,
    2
  );
  document.querySelector("#call").value = JSON.stringify({ tool: "send_sms", arguments: { to: "+2547", message: "hi" }, grant: null }, null, 2);
  document.querySelector("#score-btn").addEventListener("click", score);
  document.querySelector("#validate-btn").addEventListener("click", validate);
  document.querySelector("#status-btn").addEventListener("click", status);
  document.querySelector("#security-btn").addEventListener("click", security);
  document.querySelector("#grant-btn").addEventListener("click", grant);
});
