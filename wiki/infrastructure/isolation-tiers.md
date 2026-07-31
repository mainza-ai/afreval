---
type: infrastructure
tags: [isolation, gvisor, firecracker, envoy, sandbox]
updated: 2026-07-31
---

# Isolation Tiers

The runtime AfrEval actually executes untrusted/candidate models inside. Not itself a Karpathy Loop target except at the boundary (§3.5) — **the isolation layer should be conservatively engineered, not autonomously mutated.**

## Standard tier — gVisor

[gVisor](https://gvisor.dev) for Kubernetes-native sandboxing: a user-space kernel per workload that intercepts/filters syscalls, neutralizing privilege escalation and container drift without the shared-kernel blast radius of plain Docker. (Capability-dropped Docker is explicitly rejected as an "unacceptable blast radius.")

## High-assurance tier — Firecracker

[Firecracker](https://firecracker-microvm.github.io) microVMs: a dedicated kernel per workload with sub-second provisioning — for evaluations requiring the highest isolation tier (financial-sector and government deployments).

## Credential handling

- Synthetic enterprise credentials for tool-use testing are **injected dynamically at request time via an Envoy sidecar** — never passed directly to the agent under test.
- Agent **memory/state is destroyed on evaluation-cycle completion**, not retained.

## Related

- [Zero-Trust Sandboxing](../concepts/zero-trust-sandboxing.md) — the threat model
- [MCP Execution Boundary](mcp-execution-boundary.md) — the protocol-level layer
- [agent-airlock subsystem](../subsystems/agent-airlock.md) — the boundary hardening loop
- [Phases — Phase 2](../build-plan/phases.md) — when this is stood up
