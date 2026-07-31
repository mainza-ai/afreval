---
type: infrastructure
tags: [network, topology, latency, ttft, throughput, africa]
updated: 2026-07-31
---

# Network Topology Realism

African digital infrastructure has unique geographic and network challenges — high latency in model serving can break real-time agentic workflows and render asynchronous tools useless. AfrEval benchmarks models **under actual African network conditions**, not US-East datacenter round-trips.

## What's simulated

- **Intra-continent east-west terrestrial routes** and **subsea cable topology** — the real physics of African connectivity.
- **Time-to-First-Token (TTFT)** and **throughput degradation** measured under these simulated constraints.
- Models are forced to operate against simulated constraints matching **cloud-neutral colocation facilities in Lagos, Nairobi, and Cape Town** — the primary hubs.

## Why it matters

A model that only looks good on a US-East datacenter round-trip is **not a passing result**. Certified agents must not timeout, hallucinate, or desync when deployed in the real world.

## Related

- [Zero-Trust Sandboxing](../concepts/zero-trust-sandboxing.md) — the runtime this realism applies to
- [Enterprise SaaS & VC](../strategy/enterprise-saas.md) — the deployment context driving this requirement
