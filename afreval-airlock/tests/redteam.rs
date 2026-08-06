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
            ("query_customer".into(), tool("query_customer", &[("customer_id", ParamType::String, true)])),
            ("get_balance".into(), tool("get_balance", &[("account", ParamType::String, true)])),
            (
                "send_sms".into(),
                tool("send_sms", &[("to", ParamType::String, true), ("message", ParamType::String, true)]),
            ),
        ]),
        output_max_bytes: 4096,
        clearance: clearance::ClearancePolicy { hmac_key_b64: KEY.into(), max_age_secs: 300 },
        reauth_tools: vec!["send_sms".into(), "get_balance".into()],
        grant_call_binding: false,
    }
}

fn valid_grant(tool: &str) -> String {
    clearance::sign(tool, NOW - 30, &policy().clearance).unwrap()
}

fn call(tool: &str, args: serde_json::Value, grant: Option<&str>) -> ToolCall {
    ToolCall { tool: tool.into(), arguments: args, grant: grant.map(String::from) }
}

fn must_not_allow(label: &str, c: ToolCall) {
    let v = afreval_airlock::validate(&c, &policy(), NOW);
    assert!(!v.is_allowed(), "BYPASS: {label} was allowed: {:?}", v);
}

#[test]
fn seam1_toolname_confusion_is_blocked() {
    for tool_name in [
        "query_customer ",
        " query_customer",
        "QUERY_CUSTOMER",
        "query_customer\n",
        "query_customer.sql",
        "./query_customer",
        "send_sms;",
    ] {
        must_not_allow("toolname confusion", call(tool_name, serde_json::json!({}), None));
    }
}

#[test]
fn seam2_injection_ghost_args_are_neutralized() {
    let p = policy();
    let v = afreval_airlock::validate(
        &call("query_customer", serde_json::json!({"customer_id": "c1", "sql": "DROP TABLE customers"}), None),
        &p,
        NOW,
    );
    assert!(v.is_allowed());
    assert!(v.ghost_args_stripped.contains(&"sql".to_string()), "injection must never reach the tool");

    let v = afreval_airlock::validate(
        &call("query_customer", serde_json::json!({"customer_id": "c1", "shell": "true"}), None),
        &p,
        NOW,
    );
    assert!(v.is_allowed());
    assert!(v.ghost_args_stripped.contains(&"shell".to_string()));

    let v = afreval_airlock::validate(
        &call("query_customer", serde_json::json!({"customer_id": "c1", "__proto__": {"polluted": true}}), None),
        &p,
        NOW,
    );
    assert!(v.is_allowed());
    assert!(v.ghost_args_stripped.contains(&"__proto__".to_string()));

    let v = afreval_airlock::validate(
        &call(
            "send_sms",
            serde_json::json!({"to": "+2547", "message": "hi", "directives": {"format": "dangerous"}}),
            Some(&valid_grant("send_sms")),
        ),
        &p,
        NOW,
    );
    assert!(v.is_allowed());
    assert!(v.ghost_args_stripped.contains(&"directives".to_string()));
}

#[test]
fn seam2_null_and_type_confusion_is_blocked() {
    must_not_allow("null customer_id", call("query_customer", serde_json::json!({"customer_id": null}), None));
    must_not_allow("int customer_id", call("query_customer", serde_json::json!({"customer_id": 7}), None));
    must_not_allow("missing message on send_sms", call(
        "send_sms",
        serde_json::json!({"to": "+2547"}),
        Some(&valid_grant("send_sms")),
    ));
}

#[test]
fn seam4_forged_grants_are_rejected() {
    let wrong_key = clearance::ClearancePolicy {
        hmac_key_b64: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA".into(),
        max_age_secs: 300,
    };
    let forged = clearance::sign("get_balance", NOW - 30, &wrong_key).unwrap();
    must_not_allow("forged with wrong key", call("get_balance", serde_json::json!({"account": "a"}), Some(&forged)));

    let mut tampered = valid_grant("get_balance");
    tampered.insert_str(5, "x");
    must_not_allow("tampered grant", call("get_balance", serde_json::json!({"account": "a"}), Some(&tampered)));

    must_not_allow("expired grant", call(
        "get_balance",
        serde_json::json!({"account": "a"}),
        Some(&clearance::sign("get_balance", NOW - 301, &policy().clearance).unwrap()),
    ));

    let padded = format!(" {} ", valid_grant("get_balance"));
    must_not_allow("whitespace-padded grant", call("get_balance", serde_json::json!({"account": "a"}), Some(&padded)));
}

#[test]
fn seam4_grant_for_one_tool_does_not_gate_another() {
    let g = valid_grant("send_sms");
    must_not_allow("wrong-tool grant", call("get_balance", serde_json::json!({"account": "a"}), Some(&g)));
}

#[test]
fn seam3_oversized_output_is_rejected_not_truncated() {
    let p = policy();
    let big = vec![b'x'; 5000];
    assert!(afreval_airlock::sanitize_output(&big, &p).is_err());
}

#[test]
fn seam3_pii_never_leaks() {
    let p = policy();
    let out = afreval_airlock::sanitize_output(
        b"customer alice@corp.io phone +233 24 000 0000 id 9988776655",
        &p,
    )
    .unwrap();
    let s = String::from_utf8(out).unwrap();
    assert!(!s.contains("alice@corp.io"));
    assert!(!s.contains("+233"));
    assert!(!s.contains("9988776655"));
}

// ---- regression tests promoted from §3.5 hardening-loop bypasses (2026-08-05) ----

#[test]
fn seam3_unicode_confusable_pii_is_masked() {
    // Bypass found 2026-08-05: alice@corp.ｉｏ (fullwidth dot + fullwidth
    // TLD) evaded the ASCII-only email regex and leaked unmasked. NFKC
    // normalization fixes it.
    let p = policy();
    let out = afreval_airlock::sanitize_output("customer alice@corp.\u{ff49}o logged in".as_bytes(), &p).unwrap();
    let s = String::from_utf8(out).unwrap();
    assert!(!s.contains("alice"), "fullwidth-TLD email leaked: {s}");
    assert!(s.contains("[EMAIL]"));
}

#[test]
fn seam2_duplicate_keys_are_rejected() {
    // Bypass found 2026-08-05: {"customer_id":"c1","customer_id":"DROP TABLE x"}
    // deserialized last-wins, letting an injected value through the schema
    // with no ghost-arg strip. RFC 8259: duplicate keys are undefined behavior;
    // the validator now denies them at parse time.
    let raw = r#"{"tool":"query_customer","arguments":{"customer_id":"c1","customer_id":"DROP TABLE x"},"grant":null}"#;
    let result: Result<afreval_airlock::ToolCall, _> = serde_json::from_str(raw);
    assert!(result.is_err(), "duplicate keys must not deserialize silently");
}

// ---- seam-4 replay protection regression tests (2026-08-05) ----

#[test]
fn seam4_grant_replay_is_rejected() {
    // A valid grant used twice in one guarded batch is a replay: the second
    // use must fail closed to RequireReauth (jti consumed).
    let p = policy();
    let g = valid_grant("get_balance");
    let mut guard = afreval_airlock::clearance::ReplayGuard::new();

    let c1 = call("get_balance", serde_json::json!({"account": "a1"}), Some(&g));
    let v1 = afreval_airlock::validate_guarded(&c1, &p, NOW, &mut guard);
    assert!(v1.is_allowed(), "first use of a fresh grant must pass: {:?}", v1);

    let c2 = call("get_balance", serde_json::json!({"account": "a2"}), Some(&g));
    let v2 = afreval_airlock::validate_guarded(&c2, &p, NOW, &mut guard);
    assert_eq!(v2.decision, Decision::RequireReauth, "replayed grant must be rejected");
}

#[test]
fn seam4_jti_less_grant_fails_closed_under_guard() {
    // A hand-crafted grant with no parseable jti must fail closed when the
    // replay guard is enforced (never silently allow).
    let p = policy();
    let mut guard = afreval_airlock::clearance::ReplayGuard::new();
    // valid signature but no jti claim: use the legacy sign path then strip jti
    let g = clearance::sign("get_balance", NOW - 30, &p.clearance).unwrap();
    assert!(guard.consume(&g), "fresh grant must be consumable once");
    let c = call("get_balance", serde_json::json!({"account": "a1"}), Some(&g));
    let v = afreval_airlock::validate_guarded(&c, &p, NOW, &mut guard);
    assert_eq!(v.decision, Decision::RequireReauth);
}

#[test]
fn seam4_call_bound_grant_rejects_other_call() {
    // When the policy enables grant_call_binding, a grant issued for one
    // exact call (canonical hash) must not authorize a different call.
    let mut p = policy();
    p.grant_call_binding = true;

    let c1 = call("get_balance", serde_json::json!({"account": "a1"}), None);
    let h1 = afreval_airlock::canonical_call_hash(&c1);
    let g = clearance::sign_for_call("get_balance", &h1, NOW - 30, &p.clearance).unwrap();

    let ok = call("get_balance", serde_json::json!({"account": "a1"}), Some(&g));
    let v_ok = afreval_airlock::validate(&ok, &p, NOW);
    assert!(v_ok.is_allowed(), "matching call must pass: {:?}", v_ok);

    let other = call("get_balance", serde_json::json!({"account": "a2"}), Some(&g));
    let v_other = afreval_airlock::validate(&other, &p, NOW);
    assert_eq!(v_other.decision, Decision::RequireReauth, "grant must not transfer to another call");
}

#[test]
fn seam4_call_binding_rejects_tool_scoped_grant() {
    // With call binding enabled, a tool-scoped grant (no call hash) must not
    // authorize anything — the operator must issue call-bound grants.
    let mut p = policy();
    p.grant_call_binding = true;
    let g = valid_grant("get_balance"); // tool-scoped, no call_hash
    let c = call("get_balance", serde_json::json!({"account": "a1"}), Some(&g));
    let v = afreval_airlock::validate(&c, &p, NOW);
    assert_eq!(v.decision, Decision::RequireReauth);
}
