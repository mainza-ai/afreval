pub mod clearance;
pub mod ghost_args;
pub mod sanitize;

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Deserialize)]
pub struct ParamSchema {
    #[serde(rename = "type")]
    pub kind: ParamType,
    pub required: bool,
}

#[derive(Debug, Clone, Copy, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum ParamType {
    String,
    Integer,
    Number,
    Boolean,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ToolSchema {
    pub params: BTreeMap<String, ParamSchema>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Policy {
    pub allowed_tools: Vec<String>,
    pub schemas: BTreeMap<String, ToolSchema>,
    pub output_max_bytes: usize,
    pub clearance: clearance::ClearancePolicy,
    pub reauth_tools: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ToolCall {
    pub tool: String,
    pub arguments: serde_json::Value,
    pub grant: Option<String>,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub enum Decision {
    Allow,
    Deny,
    RequireReauth,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct Verdict {
    pub decision: Decision,
    pub reasons: Vec<String>,
}

impl Verdict {
    pub fn is_allowed(&self) -> bool {
        self.decision == Decision::Allow
    }
}

fn deny(reason: String) -> Verdict {
    Verdict {
        decision: Decision::Deny,
        reasons: vec![reason],
    }
}

fn require_reauth(reason: String) -> Verdict {
    Verdict {
        decision: Decision::RequireReauth,
        reasons: vec![reason],
    }
}

pub fn validate(call: &ToolCall, policy: &Policy, now_secs: u64) -> Verdict {
    if !policy.allowed_tools.contains(&call.tool) {
        return deny(format!("tool '{}' not in deny-by-default allowlist", call.tool));
    }
    if policy.reauth_tools.contains(&call.tool) {
        match &call.grant {
            None => return require_reauth("no context grant supplied for sensitive tool".into()),
            Some(g) => {
                if !clearance::verify_grant(g, &policy.clearance, &call.tool, now_secs) {
                    return require_reauth("context grant verification failed".into());
                }
            }
        }
    }
    let stripped = match ghost_args::validate_and_strip(&call.tool, &call.arguments, policy) {
        Ok(s) => s,
        Err(reason) => return deny(reason),
    };
    let mut reasons = vec![
        "allowlist: allowed".into(),
        "schema: validated".into(),
    ];
    if !stripped.removed.is_empty() {
        reasons.push(format!("ghost args stripped: {}", stripped.removed.join(",")));
    }
    if policy.reauth_tools.contains(&call.tool) {
        reasons.push("clearance: verified".into());
    }
    Verdict {
        decision: Decision::Allow,
        reasons,
    }
}

pub fn sanitize_output(bytes: &[u8], policy: &Policy) -> Result<Vec<u8>, String> {
    sanitize::sanitize(bytes, policy.output_max_bytes)
}
