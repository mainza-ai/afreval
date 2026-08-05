# afreval-airlock

Deny-by-default tool-call validator for Milimo AfrEval (§3.5). Rust, in-process,
zero-core-deps philosophy (mirrors `sattyamjjain/agent-airlock`, which this
subsystem builds on/extends — see the dependency note below). This is the
**zero-trust runtime hot path**, sharing Rust with `afreval-context-score`.

## The four defensive seams

| # | Seam | Behavior |
|---|---|---|
| 1 | **Deny-by-default allowlist** | Tool not in `allowed_tools` → `Deny`, first and blocking (no secondary detector invoked) |
| 2 | **Ghost-argument blocking** | Undeclared params are **stripped** (recorded in reasons); missing required params or wrong types → `Deny` |
| 3 | **Output sanitization** | Hard output cap + PII masking (email/phone/national-ID), applied to tool output before it propagates |
| 4 | **Per-call reauthorization** | Sensitive tools require a JWS HS256 clearance grant pinned to the operator trust-root key, within `max_age_secs`, bound to the exact tool |

The MCP transport + JWS clearance system is the **trust root — never mutated by
agents** (§3.5: "this is the trust root, no agent mutates it, ever").

## CLI

```bash
# sign a per-call grant for a sensitive tool (operator-side, offline)
afreval-airlock grant --policy policies/demo.json --tool send_sms --age-secs 60

# validate a tool-call JSON against the policy
afreval-airlock validate --policy policies/demo.json --call call.json
# exit 0 = Allow, 1 = Deny/RequireReauth, 2 = invalid input
```

## Usage (library)

```rust
use afreval_airlock::{validate, Policy, ToolCall};
let verdict = validate(&call, &policy, now_secs);
if verdict.is_allowed() { /* pass to the tool */ }
```

## Layout

```
src/clearance.rs  # seam 4 — JWS HS256 clearance, operator trust root (immutable)
src/allowlist.rs  # seam 1 — deny-by-default
src/ghost_args.rs # seam 2 — schema validation + ghost-arg stripping
src/sanitize.rs   # seam 3 — output cap + PII masking
src/lib.rs        # ToolCall/Policy/Verdict + validate()
src/main.rs       # CLI (grant/validate)
policies/demo.json
tests/seams.rs    # per-seam tests — every confirmed bypass becomes a regression test
```

## Hardening loop (§3.5)

The mutable artifact is the **attacker's payload-generation strategy** (a red-team
"attack program"), not the validator. Metric = **bypass rate per seam** (never
aggregated). Every confirmed bypass is added to `tests/seams.rs` as a permanent
regression test — that is what makes the loop harden the system over time.

## Hardening round 2026-08-05 — 2 bypasses found, both fixed

Attack suite expanded 20 → 31 variants (unicode homoglyphs, fullwidth confusables,
nested-ghost smuggling, capitalized/homoglyph params). Two real bypasses found,
both promoted to regression tests in `tests/redteam.rs`:

| Bypass | Root cause | Fix |
|---|---|---|
| seam 3: `alice@corp.ｉｏ` (fullwidth TLD) leaked unmasked | ASCII-only email regex evadable by unicode confusables | **NFKC normalization** before masking (`src/sanitize.rs`) |
| seam 2: duplicate keys `{"customer_id":"c1","customer_id":"DROP TABLE x"}` deserialized last-wins | RFC 8259: dup keys are undefined behavior; last-wins silently swallowed the injected value | **StrictArgs deserializer** rejects duplicate keys at parse (`src/ghost_args.rs` + custom `ToolCall` Deserialize) |

The dup-key case is covered at the wire level in the regression test; it is not
transmittable through the JS harness (`JSON.parse` collapses it first). Rebuilt:
**31 variants, 0 bypasses, 21 tests passing.**

## Dependency strategy note

The reference implementation is `sattyamjjain/agent-airlock` (deny-by-default,
Pydantic, in-process, beneath MCP gateways). It implements seams 1–3 natively;
**seam 4 (per-call reauthorization / JWS clearance) is the genuinely-unbuilt
piece this project adds.** Per the Bible, this should be a vendored/extended
fork rather than a from-scratch reimplementation — the crate here is the
standalone Rust core + seam 4; track upstream releases as a security feed.

## Related

- [agent-airlock subsystem](../wiki/subsystems/agent-airlock.md)
- [Zero-trust sandboxing](../wiki/concepts/zero-trust-sandboxing.md)
- [MCP execution boundary](../wiki/infrastructure/mcp-execution-boundary.md)
- [Phase 2 acceptance](../wiki/build-plan/phases.md)
