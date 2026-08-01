// Seam-4 trust root: the JWS clearance key material.
//
// Skeleton: reads the operator trust key from $AFREVAL_TRUST_KEY (dev fallback
// below). Production (post-MVP) replaces this with a real Stronghold vault via
// tauri-plugin-stronghold — the key must never leave encrypted storage. This
// module is the boundary: the validator never sees the key, only the clearance
// policy.

use afreval_airlock::clearance::ClearancePolicy;

const DEV_KEY: &str = "CNXxf4RhmTbsqtWMnzgPxnLARJB3Hw-zpudJpIiwxXk";

pub struct Vault {
    hmac_key: String,
    max_age_secs: u64,
}

impl Vault {
    pub fn from_env() -> Self {
        let hmac_key =
            std::env::var("AFREVAL_TRUST_KEY").unwrap_or_else(|_| DEV_KEY.to_string());
        let max_age_secs = std::env::var("AFREVAL_GRANT_MAX_AGE")
            .ok()
            .and_then(|s| s.parse().ok())
            .unwrap_or(300);
        Vault {
            hmac_key,
            max_age_secs,
        }
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
            "source": if std::env::var("AFREVAL_TRUST_KEY").is_ok() { "env" } else { "dev-fallback" },
            "max_age_secs": self.max_age_secs,
            "storage": "env/file (skeleton); tauri-plugin-stronghold lands post-MVP per report §10",
        })
    }
}
