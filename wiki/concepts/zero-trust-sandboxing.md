---
type: concept
tags: [zero-trust, sandboxing, isolation, mcp, credentials, security]
updated: 2026-07-31
---

# Zero-Trust Sandboxing

AfrEval is not a static offline benchmarking tool — it is a **live, continuous testing infrastructure** for cyber-capable agents. When a bank or government entity wants to deploy an AI agent, the agent must prove it can query databases, trigger APIs, and route financial transactions *without catastrophic vulnerabilities*. Evaluating such models demands genuinely air-gapped, hardened infrastructure, because **the evaluation sandbox itself becomes a target the model under test will actively attempt to breach.**

## Isolation tiers ([infrastructure/isolation-tiers](../infrastructure/isolation-tiers.md))

Traditional Docker containers — capability-dropped but sharing the host kernel — have an unacceptable blast radius for rogue, hallucinating agents.

- **Standard tier:** [gVisor](https://gvisor.dev) — a distinct user-space kernel per workload, intercepting/filtering syscalls; neutralizes privilege escalation, container drift, and lateral movement.
- **High-assurance tier:** [Firecracker](https://firecracker-microvm.github.io) microVMs — a dedicated kernel per workload with sub-second provisioning, for financial-sector and government deployments.
- **Credentials:** synthetic enterprise credentials for tool-use testing are injected dynamically at request time via an **Envoy sidecar** — never passed directly to the agent under test — and memory/state is destroyed on evaluation-cycle completion, not retained.

## The four defensive seams (execution boundary)

Evaluated via the Model Context Protocol ("USB-C for agentic AI") and enforced by [agent-airlock](../subsystems/agent-airlock.md):

1. **Deny-by-default tool allowlist** — a camouflaged directive targeting an unlisted tool is blocked without ever invoking a secondary detector.
2. **Ghost-argument blocking** — an agent cannot smuggle undeclared parameters past validation.
3. **Output sanitization** — hard output caps plus PII masking, so camouflaged directives embedded in tool outputs can't propagate.
4. **Per-call reauthorization** — explicit context grants from the harness to break multi-agent fan-out or debate-amplification loops.

At the **transport layer**, message signatures and nonces are validated against a canonical schema (mitigating insecure-deserialization RCE), and a **JSON Web Signature (JWS) compact clearance** system gates tool invocation against an offline-signed, operator-trust-root-pinned assertion.

## Related

- [Isolation Tiers](../infrastructure/isolation-tiers.md)
- [MCP Execution Boundary](../infrastructure/mcp-execution-boundary.md)
- [agent-airlock subsystem](../subsystems/agent-airlock.md)
- [Karpathy Loop](karpathy-loop.md) — the isolation layer itself is *not* a loop target; it's conservatively engineered
