use afreval_airlock::clearance;
use afreval_airlock::{Decision, ParamSchema, ParamType, Policy, ToolCall, ToolSchema};
use std::collections::BTreeMap;

const KEY: &str = "CNXxf4RhmTbsqtWMnzgPxnLARJB3Hw-zpudJpIiwxXk";
const NOW: u64 = 1_000_000_000;

fn tool(name: &str, params: &[(&str, ParamType, bool)]) -> ToolSchema {
    let mut m = BTreeMap::new();
    for (n, t, r) in params {
        m.insert((*n).into(), ParamSchema { kind: *t, required: *r });
    }
    ToolSchema { params: m }
}

fn policy() -> Policy {
    Policy {
        allowed_tools: vec!["query_customer".into(), "get_balance".into(), "send_sms".into()],
        schemas: BTreeMap::from([
            (
                "query_customer".into(),
                tool("query_customer", &[("customer_id", ParamType::String, true)]),
            ),
            ("get_balance".into(), tool("get_balance", &[("account", ParamType::String, true)])),
            (
                "send_sms".into(),
                tool("send_sms", &[("to", ParamType::String, true), ("message", ParamType::String, true)]),
            ),
        ]),
        output_max_bytes: 4096,
        clearance: clearance::ClearancePolicy {
            hmac_key_b64: KEY.into(),
            max_age_secs: 300,
        },
        reauth_tools: vec!["send_sms".into(), "get_balance".into()],
        grant_call_binding: false,
    }
}

fn call(tool: &str, args: serde_json::Value, grant: Option<&str>) -> ToolCall {
    ToolCall {
        tool: tool.into(),
        arguments: args,
        grant: grant.map(|s| s.to_string()),
    }
}

#[test]
fn seam1_unlisted_tool_is_denied_without_secondary_checks() {
    let c = call("rm_rf", serde_json::json!({"path": "/"}), None);
    let v = afreval_airlock::validate(&c, &policy(), NOW);
    assert_eq!(v.decision, Decision::Deny);
    assert!(v.reasons[0].contains("allowlist"));
}

#[test]
fn seam2_ghost_args_are_stripped_but_call_allowed() {
    let c = call(
        "query_customer",
        serde_json::json!({"customer_id": "c1", "sql": "DROP TABLE customers", "--flag": true}),
        None,
    );
    let v = afreval_airlock::validate(&c, &policy(), NOW);
    assert!(v.is_allowed());
    assert!(v.reasons.iter().any(|r| r.contains("ghost args stripped")));
}

#[test]
fn seam2_missing_required_param_is_denied() {
    let c = call("query_customer", serde_json::json!({}), None);
    let v = afreval_airlock::validate(&c, &policy(), NOW);
    assert_eq!(v.decision, Decision::Deny);
    assert!(v.reasons[0].contains("required param"));
}

#[test]
fn seam2_wrong_type_is_denied() {
    let c = call("query_customer", serde_json::json!({"customer_id": 42}), None);
    let v = afreval_airlock::validate(&c, &policy(), NOW);
    assert_eq!(v.decision, Decision::Deny);
}

#[test]
fn seam3_pii_is_masked() {
    let policy = policy();
    let out = afreval_airlock::sanitize_output(
        b"contact alice@example.com or +254 712 345 678, id 12345678",
        &policy,
    )
    .unwrap();
    let s = String::from_utf8(out).unwrap();
    assert!(!s.contains("alice@example.com"));
    assert!(s.contains("[EMAIL]"));
    assert!(s.contains("[PHONE]"));
    assert!(s.contains("[ID]"));
}

#[test]
fn seam3_output_over_cap_is_rejected() {
    let mut p = policy();
    p.output_max_bytes = 8;
    assert!(afreval_airlock::sanitize_output(b"this is too long", &p).is_err());
}

#[test]
fn seam4_valid_grant_passes_reauth() {
    let p = policy();
    let grant = clearance::sign("get_balance", NOW - 60, &p.clearance).unwrap();
    let c = call("get_balance", serde_json::json!({"account": "a1"}), Some(&grant));
    let v = afreval_airlock::validate(&c, &p, NOW);
    assert!(v.is_allowed());
}

#[test]
fn seam4_missing_grant_requires_reauth() {
    let c = call("get_balance", serde_json::json!({"account": "a1"}), None);
    let v = afreval_airlock::validate(&c, &policy(), NOW);
    assert_eq!(v.decision, Decision::RequireReauth);
}

#[test]
fn seam4_tampered_grant_is_rejected() {
    let p = policy();
    let mut grant = clearance::sign("get_balance", NOW - 60, &p.clearance).unwrap();
    grant.push('x');
    let c = call("get_balance", serde_json::json!({"account": "a1"}), Some(&grant));
    let v = afreval_airlock::validate(&c, &p, NOW);
    assert_eq!(v.decision, Decision::RequireReauth);
}

#[test]
fn seam4_wrong_tool_grant_is_rejected() {
    let p = policy();
    let grant = clearance::sign("send_sms", NOW - 60, &p.clearance).unwrap();
    let c = call("get_balance", serde_json::json!({"account": "a1"}), Some(&grant));
    let v = afreval_airlock::validate(&c, &p, NOW);
    assert_eq!(v.decision, Decision::RequireReauth);
}

#[test]
fn seam4_expired_grant_is_rejected() {
    let p = policy();
    let grant = clearance::sign("get_balance", NOW - 301, &p.clearance).unwrap();
    let c = call("get_balance", serde_json::json!({"account": "a1"}), Some(&grant));
    let v = afreval_airlock::validate(&c, &p, NOW);
    assert_eq!(v.decision, Decision::RequireReauth);
}

#[test]
fn non_reauth_tool_does_not_need_grant() {
    let c = call("query_customer", serde_json::json!({"customer_id": "c1"}), None);
    let v = afreval_airlock::validate(&c, &policy(), NOW);
    assert!(v.is_allowed());
}
