// Seam-4 trust root: the JWS clearance key material.
//
// Sources, in order: $AFREVAL_TRUST_KEY_FILE (file) -> $AFREVAL_TRUST_KEY (env)
// -> DEV fallback, and the DEV fallback is ONLY available in debug builds.
// In release builds the vault FAILS CLOSED if no real key is configured — a
// certification client must never silently sign with a well-known dev key
// (gap-analysis G3/O1, 2026-08-05). Stronghold (tauri-plugin-stronghold)
// remains the post-MVP encrypted-storage replacement per report §10.

use afreval_airlock::clearance::ClearancePolicy;

const DEV_KEY: &str = "CNXxf4RhmTbsqtWMnzgPxnLARJB3Hw-zpudJpIiwxXk";

pub struct Vault {
    hmac_key: String,
    source: &'static str,
    max_age_secs: u64,
}

impl Vault {
    /// Loads the trust key. In a release build with no configured key this
    /// returns Err — the caller must not proceed (fail closed).
    pub fn from_env() -> Result<Self, String> {
        let file = std::env::var("AFREVAL_TRUST_KEY_FILE").ok();
        if let Some(p) = file {
            let trimmed = std::fs::read_to_string(&p)
                .map_err(|e| format!("read {}: {e}", p))?
                .trim()
                .to_string();
            if !trimmed.is_empty() {
                return Self::with_key(trimmed, "file", 300);
            }
        }
        if let Ok(k) = std::env::var("AFREVAL_TRUST_KEY") {
            if !k.trim().is_empty() {
                return Self::with_key(k.trim().to_string(), "env", 300);
            }
        }
        if cfg!(debug_assertions) {
            Ok(Self::with_key(DEV_KEY.to_string(), "dev-fallback", 300).unwrap())
        } else {
            Err("no trust key configured: set AFREVAL_TRUST_KEY_FILE or AFREVAL_TRUST_KEY "
                .to_string()
                .trim_end()
                .to_string())
        }
    }

    fn with_key(key: String, source: &'static str, default_max_age: u64) -> Result<Self, String> {
        let max_age_secs = std::env::var("AFREVAL_GRANT_MAX_AGE")
            .ok()
            .and_then(|s| s.parse().ok())
            .unwrap_or(default_max_age);
        Ok(Vault {
            hmac_key: key,
            source,
            max_age_secs,
        })
    }

    pub fn clearance_policy(&self) -> ClearancePolicy {
        ClearancePolicy {
            hmac_key_b64: self.hmac_key.clone(),
            max_age_secs: self.max_age_secs,
        }
    }

    pub fn status(&self) -> serde_json::Value {
        serde_json::json!({
            "trust_root_configured": true,
            "source": self.source,
            "max_age_secs": self.max_age_secs,
            "storage": if self.source == "dev-fallback" {
                "DEV ONLY — debug builds only; set AFREVAL_TRUST_KEY_FILE in production"
            } else {
                "env/file; tauri-plugin-stronghold lands post-MVP per report §10"
            },
        })
    }
}
