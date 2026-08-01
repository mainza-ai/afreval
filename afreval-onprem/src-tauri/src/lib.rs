// afreval-onprem — air-gapped certification + security dashboard client.
// Embeds the deterministic Context Score scorer and the airlock validator as
// Rust crates. The UI surface is the reuse target for afreval-dashboard.

use afreval_airlock::{clearance, Policy, ToolCall};
use afreval_context_score::{config, report, score};

#[tauri::command]
fn score_report(report_json: String, weights_yaml: String) -> Result<String, String> {
    let rep = report::ModelReport::from_json(&report_json)?;
    rep.validate()?;
    let cfg = config::VerticalConfig::from_yaml(&weights_yaml)?;
    cfg.validate()?;
    let s = score::score(&rep, &cfg);
    let out = serde_json::json!({
        "model_id": rep.model_id,
        "vertical": cfg.vertical,
        "context_score": s.context_score,
        "linguistic_fidelity": s.linguistic_fidelity,
        "cultural_safety": s.cultural_safety,
        "structural_economics": s.structural_economics,
        "pass": s.pass,
    });
    Ok(serde_json::to_string_pretty(&out).map_err(|e| e.to_string())?)
}

#[tauri::command]
fn validate_tool_call(call_json: String, policy_json: String) -> Result<String, String> {
    let call: ToolCall = serde_json::from_str(&call_json).map_err(|e| e.to_string())?;
    let policy: Policy = serde_json::from_str(&policy_json).map_err(|e| e.to_string())?;
    let verdict = afreval_airlock::validate(&call, &policy, clearance::now_secs());
    Ok(serde_json::to_string_pretty(&verdict).map_err(|e| e.to_string())?)
}

#[tauri::command]
fn clearance_status() -> Result<String, String> {
    let out = serde_json::json!({
        "trust_root_configured": false,
        "note": "Stronghold vault (JWS key material) lands post-MVP per report §10",
    });
    Ok(serde_json::to_string_pretty(&out).map_err(|e| e.to_string())?)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            score_report,
            validate_tool_call,
            clearance_status
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
