---
type: infrastructure
tags: [mcp, protocol, jwt, jws, tool-calls, execution-boundary]
updated: 2026-07-31
---

# MCP Execution Boundary

The **Model Context Protocol** is the standard connective tissue linking probabilistic language models with deterministic digital systems — "USB-C for agentic AI." AfrEval uses it to probe how a candidate agent interacts with external enterprise tools, enforcing integrity at two layers.

## Runtime layer — agent-airlock

Tools are protected by [agent-airlock](../subsystems/agent-airlock.md), a deny-by-default execution boundary validating the precise payloads the model produces before they interact with internal APIs. Because LLMs hallucinate tool calls daily (inventing non-existent arguments, sending strings where integers are required), AfrEval tests agents against **four structural defensive seams**:

1. **Deny-by-default tool allowlist** — a camouflaged directive targeting an unlisted tool is blocked without invoking a secondary detector.
2. **Ghost-argument blocking** — no smuggling undeclared parameters past validation.
3. **Strict output sanitization** — hard output caps + PII masking so camouflaged directives embedded in tool outputs can't propagate.
4. **Per-call reauthorization** — explicit context grants from the harness to break multi-agent fan-out or debate-amplification loops.

Plus the **Server-Card trust boundary**: tool descriptions fetched from MCP server cards are attacker-influenceable content, routed through the same `ToolOutputTrustGuard` as untrusted tool output — a poisoned description is treated as an injection into the agent's context, not a config value.

## Transport layer — message signature / JWS clearance

- Validate **message signatures and nonces against a canonical schema** — mitigates insecure-deserialization vulnerabilities that frequently lead to remote code execution.
- A **JSON Web Signature (JWS) compact clearance** system guarantees an agent can only invoke tools corresponding to an offline-signed clearance assertion **pinned to an operator's trust root**.

## Related

- [Zero-Trust Sandboxing](../concepts/zero-trust-sandboxing.md)
- [agent-airlock subsystem](../subsystems/agent-airlock.md) — the hardening loop over this boundary
- [Isolation Tiers](isolation-tiers.md) — the kernel/microVM layer beneath
- [Phases — Phase 2](../build-plan/phases.md)
