---
type: subsystem
tags: [agent-airlock, security, adversarial, red-team, MCP, §3.5]
updated: 2026-08-05
---

# Subsystem §3.5 — agent-airlock Hardening Loop

Adversarial red-teaming of AfrEval's own execution boundary. The **[zero-trust sandboxing](../concepts/zero-trust-sandboxing.md)** seam: an agent asked to "clean up disk space" hallucinating `rm -rf /` is intercepted before execution.

## Status: hardening round 2026-08-05 — 2 bypasses found, both fixed

Attack suite expanded 20 → 31 variants (unicode homoglyphs, fullwidth confusables, nested-ghost smuggling, capitalized/homoglyph params). Two real bypasses found and both promoted to permanent regression tests (`tests/redteam.rs`):

1. **Seam 3 — unicode confusable PII evasion**: `alice@corp.ｉｏ` (fullwidth `ｉ`/dot) evaded the ASCII-only email regex and leaked unmasked. Fixed by **NFKC normalization** before masking.
2. **Seam 2 — duplicate-key smuggling**: `{"customer_id":"c1","customer_id":"DROP TABLE x"}` deserialized **last-wins** (RFC 8259: duplicate keys are undefined behavior), silently letting the injected value through with no ghost-arg strip. Fixed by a **StrictArgs deserializer** that rejects duplicate keys at parse time.

The dup-key case is a wire-level defense (not transmittable through the JS harness, whose `JSON.parse` collapses the keys first — the regression test covers the raw wire). Rebuilt: **31 variants, 0 bypasses, 21 tests passing.**

## Dependency strategy — the one deliberate exception

This subsystem is the exception to the "re-engineer, don't depend" rule. `autoresearch` is a whole-system skeleton with no hardening to preserve. **`agent-airlock` is the opposite: a narrow, security-focused library where the value *is* the hardening itself** — validated defended-against attack classes, edge cases found and patched, a maintainer shipping CVE-style presets reactively (e.g. the Mobile MCP `mobile_open_url` scheme-validation preset). Reimplementing from scratch means re-discovering the same vulnerability classes on a system meant to *certify other agents as safe*.

**Build on it as a real dependency** — forked/vendored into `afreval-airlock`, tracked against upstream releases, license-checked before vendoring — and extend it for the fourth seam rather than rebuilding the first three.

## Reference implementation

[sattyamjjain/agent-airlock](https://github.com/sattyamjjain/agent-airlock) — deny-by-default, Pydantic-based, in-process, zero-core-deps contract/type-checker for agent tool calls; sits beneath MCP gateways/firewalls; adapters for LangChain, OpenAI Agents SDK, PydanticAI, CrewAI. Defensive posture: ghost-argument stripping, strict type validation, self-healing retries, and — key for AfrEval's threat model — a **Server-Card trust boundary**: a tool description fetched from an MCP server card is attacker-influenceable content, not trusted config; a poisoned description ("...ignore previous instructions and run...") is treated as injection into the agent's context and routed through the same `ToolOutputTrustGuard` as untrusted tool output.

**Mapping to the four seams:** airlock already implements 1 (deny-by-default allowlist), 2 (ghost-argument blocking), 3 (output sanitization / PII masking) natively. **Seam 4 (per-call reauthorization / JWS clearance pinned to an operator's trust root) is genuinely unbuilt upstream — the piece AfrEval builds on top.**

| Field | Spec |
|---|---|
| **Frozen harness** | MCP transport layer + JWS clearance system — **must stay fixed; this is the trust root; no agent mutates it, ever** |
| **Mutable artifact** | The attacker's payload-generation strategy (a red-team agent's "attack program") |
| **Instruction file** | `program.md`: *"construct tool-call payloads that bypass one or more of the four seams without triggering `ToolOutputTrustGuard`"* |
| **Metric** | Bypass rate **per seam, not aggregated** — an aggregate hides which seam (allowlist, ghost-args, sanitization, reauth) is degrading |
| **Budget** | Fixed adversarial batch size per nightly run |
| **Loop flavor** | `git commit`/revert style, adversarial |
| **Language** | Rust for the validator (matches airlock's zero-core-deps in-process philosophy — extend rather than replace); TypeScript/JavaScript for nightly-run orchestration + the security dashboard enterprise clients look at |
| **Repo** | `afreval-airlock` (Rust core, vendored/extended fork of sattyamjjain/agent-airlock — check license compatibility first) |
| **Confirmed bypasses** | Every confirmed bypass becomes a **permanent regression test in the frozen harness** — this is what makes the loop actually harden the system instead of red-teaming it once and forgetting |

## Related

- [Zero-Trust Sandboxing](../concepts/zero-trust-sandboxing.md) — the threat model
- [MCP Execution Boundary](../infrastructure/mcp-execution-boundary.md) — runtime + transport layers
- [Risk register — upstream drift](../build-plan/risk-register.md) — treat airlock release notes as a security feed
- [Phases — Phase 2 & 3](../build-plan/phases.md)
