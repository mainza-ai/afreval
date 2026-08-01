use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;

#[derive(Debug, Clone, Deserialize)]
pub struct ClearancePolicy {
    pub hmac_key_b64: String,
    pub max_age_secs: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct GrantPayload {
    tool: String,
    iat: u64,
}

fn key(policy: &ClearancePolicy) -> Result<Vec<u8>, String> {
    URL_SAFE_NO_PAD
        .decode(&policy.hmac_key_b64)
        .map_err(|e| format!("bad hmac key: {e}"))
}

fn b64url(data: &[u8]) -> String {
    URL_SAFE_NO_PAD.encode(data)
}

fn b64url_decode(s: &str) -> Option<Vec<u8>> {
    URL_SAFE_NO_PAD.decode(s).ok()
}

pub fn sign(tool: &str, iat_secs: u64, policy: &ClearancePolicy) -> Result<String, String> {
    use hmac::{Hmac, Mac};
    type H = Hmac<sha2::Sha256>;
    let header = b64url(br#"{"alg":"HS256","typ":"JWS"}"#);
    let payload = b64url(&serde_json::to_vec(&GrantPayload { tool: tool.into(), iat: iat_secs }).unwrap());
    let signing_input = format!("{header}.{payload}");
    let mut mac = H::new_from_slice(&key(policy)?).map_err(|e| e.to_string())?;
    mac.update(signing_input.as_bytes());
    let sig = b64url(&mac.finalize().into_bytes());
    Ok(format!("{signing_input}.{sig}"))
}

pub fn verify_grant(grant: &str, policy: &ClearancePolicy, tool: &str, now_secs: u64) -> bool {
    use hmac::{Hmac, Mac};
    type H = Hmac<sha2::Sha256>;
    let parts: Vec<&str> = grant.split('.').collect();
    if parts.len() != 3 {
        return false;
    }
    let signing_input = format!("{}.{}", parts[0], parts[1]);
    let key = match key(policy) {
        Ok(k) => k,
        Err(_) => return false,
    };
    let mut mac = match H::new_from_slice(&key) {
        Ok(m) => m,
        Err(_) => return false,
    };
    mac.update(signing_input.as_bytes());
    let expected = mac.finalize().into_bytes();
    let provided = match b64url_decode(parts[2]) {
        Some(p) => p,
        None => return false,
    };
    if provided != expected.as_slice() {
        return false;
    }
    let payload = match b64url_decode(parts[1]) {
        Some(p) => p,
        None => return false,
    };
    let gp: GrantPayload = match serde_json::from_slice(&payload) {
        Ok(g) => g,
        Err(_) => return false,
    };
    if gp.tool != tool {
        return false;
    }
    now_secs.saturating_sub(gp.iat) <= policy.max_age_secs
}

pub fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}
