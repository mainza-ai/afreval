---
type: infrastructure
tags: [isolation, gvisor, firecracker, envoy, podman, seccomp, sandbox]
updated: 2026-08-05
---

# Isolation Tiers

The runtime AfrEval actually executes untrusted/candidate models inside. Not itself a Karpathy Loop target except at the boundary (§3.5) — **the isolation layer should be conservatively engineered, not autonomously mutated.**

## Standard tier — gVisor

[gVisor](https://gvisor.dev) for Kubernetes-native sandboxing: a user-space kernel per workload that intercepts/filters syscalls, neutralizing privilege escalation and container drift without the shared-kernel blast radius of plain Docker. (Capability-dropped Docker is explicitly rejected as an "unacceptable blast radius.")

## High-assurance tier — Firecracker

[Firecracker](https://firecracker-microvm.github.io) microVMs: a dedicated kernel per workload with sub-second provisioning — for evaluations requiring the highest isolation tier (financial-sector and government deployments).

## Docker-runnable substitute: Podman + seccomp/AppArmor (2026-08-05)

gVisor (`runsc`) and Firecracker both require **KVM** (Linux kernel virtualization, `/dev/kvm`). Docker Desktop on macOS/aarch64 does **not** expose KVM (no nested virtualization), so neither can run here. The open-source, Docker-compatible substitute — validated in this workspace — is:

- **Podman** (OCI runtime, drop-in Docker-compatible, no KVM) + hardened **seccomp/AppArmor** profiles for syscall filtering. This is a *reduced-guarantee* tier vs gVisor (shared kernel, so not as strong), but it is the strongest isolation available without KVM. gVisor/Firecracker remain the server-class target on real Linux hosts.

Implemented in `afreval-isolation/` (Docker/rootless-podman compose + a hardened seccomp profile + a demo workload proving the boundary).

## Credential handling

- Synthetic enterprise credentials for tool-use testing are **injected dynamically at request time via an Envoy sidecar** — never passed directly to the agent under test. Verified live in Docker (2026-08-05, `afreval-envoy/`).
- Agent **memory/state is destroyed on evaluation-cycle completion**, not retained.

## Related

- [Zero-Trust Sandboxing](../concepts/zero-trust-sandboxing.md) — the threat model
- [MCP Execution Boundary](mcp-execution-boundary.md) — the protocol-level layer
- [agent-airlock subsystem](../subsystems/agent-airlock.md) — the boundary hardening loop
- [Phases — Phase 2](../build-plan/phases.md) — when this is stood up
- [Gap analysis — E1](../build-plan/gap-analysis.md) — Docker feasibility of the tiers
