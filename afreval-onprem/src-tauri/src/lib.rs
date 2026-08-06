// afreval-onprem — air-gapped certification + security dashboard client.
// Embeds the deterministic Context Score scorer and the airlock validator as
// Rust crates. The UI surface is the reuse target for afreval-dashboard.

mod vault;

use afreval_airlock::{clearance, Policy, ToolCall};
use afreval_context_score::{config, report, score};
use vault::Vault;

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
fn clearance_status(vault: tauri::State<Vault>) -> Result<String, String> {
    Ok(serde_json::to_string_pretty(&vault.status()).map_err(|e| e.to_string())?)
}

#[tauri::command]
fn sign_grant(tool: String, vault: tauri::State<Vault>) -> Result<String, String> {
    let iat = clearance::now_secs();
    clearance::sign(&tool, iat, &vault.clearance_policy())
}

#[tauri::command]
fn security_report() -> Result<String, String> {
    // Per-seam bypass rates from the last §3.5 hardening-loop run.
    // Path: $AFREVAL_SECURITY_REPORT or <repo>/afreval-airlock/attack/report.json.
    let manifest = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let default = manifest
        .parent()
        .and_then(|p| p.parent())
        .map(|p| p.join("afreval-airlock/attack/report.json"))
        .ok_or_else(|| "cannot resolve repo root".to_string())?;
    let path = std::env::var("AFREVAL_SECURITY_REPORT")
        .map(std::path::PathBuf::from)
        .unwrap_or(default);
    let s = std::fs::read_to_string(&path).map_err(|e| format!("read {}: {e}", path.display()))?;
    Ok(s)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Fail closed: without a real trust key the client must not start (release
    // builds only accept file/env keys — the dev fallback is debug-only).
    let vault = match Vault::from_env() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("afreval-onprem: {e}");
            std::process::exit(2);
        }
    };
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(vault)
        .invoke_handler(tauri::generate_handler![
            score_report,
            validate_tool_call,
            clearance_status,
            security_report,
            sign_grant
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
