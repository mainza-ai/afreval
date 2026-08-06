pub mod clearance;
pub mod ghost_args;
pub mod sanitize;

use serde::{Deserialize, Deserializer, Serialize};
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
    /// When true, a grant must be bound to the exact call (canonical hash of
    /// tool+args), not just the tool — closes grant redirection across calls.
    #[serde(default)]
    pub grant_call_binding: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub struct ToolCall {
    pub tool: String,
    pub arguments: serde_json::Value,
    pub grant: Option<String>,
}

// Strict-args deserializer: reject duplicate keys in `arguments` (last-wins
// would let an injected value through — seam-2 finding 2026-08-05).
impl<'de> Deserialize<'de> for ToolCall {
    fn deserialize<D>(d: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        #[derive(Deserialize)]
        struct Raw {
            tool: String,
            arguments: ghost_args::StrictArgs,
            grant: Option<String>,
        }
        let raw = Raw::deserialize(d)?;
        Ok(ToolCall {
            tool: raw.tool,
            arguments: raw.arguments.0,
            grant: raw.grant,
        })
    }
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
    pub ghost_args_stripped: Vec<String>,
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
        ghost_args_stripped: Vec::new(),
    }
}

fn require_reauth(reason: String) -> Verdict {
    Verdict {
        decision: Decision::RequireReauth,
        reasons: vec![reason],
        ghost_args_stripped: Vec::new(),
    }
}

pub fn validate(call: &ToolCall, policy: &Policy, now_secs: u64) -> Verdict {
    validate_impl(call, policy, now_secs, None)
}

/// Canonical hash of a tool call (tool + sorted arguments). Used to bind a
/// grant to one exact call (seam-4 replay protection, 2026-08-05).
pub fn canonical_call_hash(call: &ToolCall) -> String {
    use std::collections::BTreeMap;
    let mut args = BTreeMap::new();
    if let Some(obj) = call.arguments.as_object() {
        for (k, v) in obj {
            args.insert(k.clone(), v.clone());
        }
    }
    let canonical = serde_json::json!({"tool": call.tool, "arguments": args});
    let input = serde_json::to_string(&canonical).unwrap_or_default();
    let digest = <sha2::Sha256 as sha2::Digest>::digest(input.as_bytes());
    format!("{digest:x}")
}

/// Validate with seam-4 replay protection: each grant's `jti` may be consumed
/// once. A replayed (or jti-less) grant fails closed to RequireReauth.
pub fn validate_guarded(
    call: &ToolCall,
    policy: &Policy,
    now_secs: u64,
    guard: &mut clearance::ReplayGuard,
) -> Verdict {
    let verdict = validate_impl(call, policy, now_secs, Some(guard));
    verdict
}

fn validate_impl(
    call: &ToolCall,
    policy: &Policy,
    now_secs: u64,
    mut guard: Option<&mut clearance::ReplayGuard>,
) -> Verdict {
    if !policy.allowed_tools.contains(&call.tool) {
        return deny(format!("tool '{}' not in deny-by-default allowlist", call.tool));
    }
    if policy.reauth_tools.contains(&call.tool) {
        match &call.grant {
            None => return require_reauth("no context grant supplied for sensitive tool".into()),
            Some(g) => {
                if let Some(gr) = guard.as_deref_mut() {
                    // replay guard is enforced: jti must be fresh AND present
                    if !gr.consume(g) {
                        return require_reauth("context grant is a replay (jti already consumed)".into());
                    }
                }
                let ok = if policy.grant_call_binding {
                    let h = canonical_call_hash(call);
                    clearance::verify_grant_bound(g, &policy.clearance, &call.tool, &h, now_secs)
                } else {
                    clearance::verify_grant(g, &policy.clearance, &call.tool, now_secs)
                };
                if !ok {
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
        ghost_args_stripped: stripped.removed,
    }
}

pub fn sanitize_output(bytes: &[u8], policy: &Policy) -> Result<Vec<u8>, String> {
    sanitize::sanitize(bytes, policy.output_max_bytes)
}
