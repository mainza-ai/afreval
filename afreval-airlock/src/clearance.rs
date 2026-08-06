use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::sync::atomic::{AtomicU64, Ordering};
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
    #[serde(default)]
    jti: String, // unique per-grant nonce — closes tool+iat replay (2026-08-05)
    #[serde(default)]
    call_hash: String, // optional exact-call binding; empty = tool-scoped grant
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

static NONCE_CTR: AtomicU64 = AtomicU64::new(0);

fn fresh_jti() -> String {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let ctr = NONCE_CTR.fetch_add(1, Ordering::Relaxed);
    format!("{nanos:x}-{ctr:x}")
}

fn sign_with(tool: &str, iat_secs: u64, policy: &ClearancePolicy, call_hash: &str) -> Result<String, String> {
    use hmac::{Hmac, Mac};
    type H = Hmac<sha2::Sha256>;
    let header = b64url(br#"{"alg":"HS256","typ":"JWS"}"#);
    let payload = GrantPayload {
        tool: tool.into(),
        iat: iat_secs,
        jti: fresh_jti(),
        call_hash: call_hash.into(),
    };
    let payload = b64url(&serde_json::to_vec(&payload).unwrap());
    let signing_input = format!("{header}.{payload}");
    let mut mac = H::new_from_slice(&key(policy)?).map_err(|e| e.to_string())?;
    mac.update(signing_input.as_bytes());
    let sig = b64url(&mac.finalize().into_bytes());
    Ok(format!("{signing_input}.{sig}"))
}

pub fn sign(tool: &str, iat_secs: u64, policy: &ClearancePolicy) -> Result<String, String> {
    sign_with(tool, iat_secs, policy, "")
}

/// Sign a grant bound to one exact call (canonical hash of tool+args). A
/// grant carrying a `call_hash` is only valid when presented with that call.
pub fn sign_for_call(tool: &str, call_hash: &str, iat_secs: u64, policy: &ClearancePolicy) -> Result<String, String> {
    sign_with(tool, iat_secs, policy, call_hash)
}

fn decode_payload(grant: &str) -> Option<GrantPayload> {
    let parts: Vec<&str> = grant.split('.').collect();
    if parts.len() != 3 {
        return None;
    }
    b64url_decode(parts[1]).and_then(|p| serde_json::from_slice(&p).ok())
}

/// Signature + tool + expiry check. `expected_call_hash` empty = tool-scoped
/// grant (no call binding); non-empty = the grant MUST carry that hash.
pub fn verify_grant(grant: &str, policy: &ClearancePolicy, tool: &str, now_secs: u64) -> bool {
    verify_grant_bound(grant, policy, tool, "", now_secs)
}

pub fn verify_grant_bound(
    grant: &str,
    policy: &ClearancePolicy,
    tool: &str,
    expected_call_hash: &str,
    now_secs: u64,
) -> bool {
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
    let gp: GrantPayload = match b64url_decode(parts[1]).and_then(|p| serde_json::from_slice(&p).ok()) {
        Some(g) => g,
        None => return false,
    };
    if gp.tool != tool {
        return false;
    }
    // Exact-call binding: a grant that embeds a call_hash must be presented
    // with that same call hash; a call-scoped verify must reject tool-scoped
    // grants too.
    if !expected_call_hash.is_empty() {
        if gp.call_hash.is_empty() || gp.call_hash != expected_call_hash {
            return false;
        }
    }
    now_secs.saturating_sub(gp.iat) <= policy.max_age_secs
}

/// Per-grant replay guard. A grant's `jti` may be consumed exactly once;
/// presenting the same grant again is a replay and is rejected. ReplayGuard
/// is runtime state owned by the caller (the airlock hot path / batch runner).
#[derive(Default)]
pub struct ReplayGuard {
    seen: HashSet<String>,
}

impl ReplayGuard {
    pub fn new() -> Self {
        Self { seen: HashSet::new() }
    }

    /// Returns false if the grant's jti was already consumed (replay).
    /// Grants without a parseable jti are treated as replayable-unsafe and
    /// rejected when the guard is enforced (fail closed).
    pub fn consume(&mut self, grant: &str) -> bool {
        match decode_payload(grant) {
            Some(p) if !p.jti.is_empty() => self.seen.insert(p.jti),
            _ => false,
        }
    }

    /// True when this grant was already consumed (i.e. a replay).
    pub fn is_replay(&self, grant: &str) -> bool {
        match decode_payload(grant) {
            Some(p) => self.seen.contains(&p.jti),
            None => true,
        }
    }
}

pub fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}
