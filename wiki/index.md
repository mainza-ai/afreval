---
type: overview
tags: [index, navigation]
updated: 2026-07-31
---

# Wiki Index

Content catalog for the Milimo AfrEval wiki. Organized by category. Read this first on any query, then drill into pages.

## Core

- [Home](home.md) — project overview and landing page
- [Synthesis](synthesis.md) — evolving cross-source synthesis, open questions, flagged discrepancies
- [Schema (AGENTS.md)](AGENTS.md) — wiki structure and maintenance conventions
- [Log](log.md) — chronological activity record

## Concepts

- [Karpathy Loop](concepts/karpathy-loop.md) — the design pattern: frozen harness + mutable artifact + instruction file + metric + budget; canonical, generalized, and platform-caveat forms
- [African Language Tax](concepts/african-language-tax.md) — tokenization fertility premiums across frontier models (up to ~9× for N'Ko), the economic penalty behind Structural Economics
- [LLM-as-Judge Bias](concepts/llm-as-judge-bias.md) — uncertainty-driven generosity on low-resource languages; pairwise-accuracy blind spot; the 43% acceptance-rate gap
- [Code-Mixing](concepts/code-mixing.md) — CMI, enhanced CMI with switch points, I-index, M-index
- [Context Score](concepts/context-score.md) — the 0–100 core IP composite: Linguistic Fidelity × Cultural Safety × Structural Economics
- [Zero-Trust Sandboxing](concepts/zero-trust-sandboxing.md) — gVisor/Firecracker isolation, Envoy credential injection, MCP, JWS clearance

## Substrates (frozen eval harnesses)

- [WAXAL](substrates/waxal.md) — acoustic substrate: ~1,250h ASR, image-prompted elicitation, WAXAL-NET baselines; includes the §2.1.1 acquisition/QA task list
- [AfroBench](substrates/afrobench.md) — textual/reasoning substrate: 64 languages, 15 tasks, 22 datasets; AfroBench-LITE; empirical findings
- [afri-fertility](substrates/afri-fertility.md) — tokenization economics engine: CPT/BPT/fertility/premium; 23 languages, 14 tokenizers; privacy posture

## Subsystems (six Karpathy Loops, §3)

- [Tokenizer & Vocab Search](subsystems/tokenizer-search.md) — §3.1, training-style loop
- [Context Score Calibration](subsystems/context-score-calibration.md) — §3.2, git-commit/revert loop; certification vs. calibration separation
- [BiasScope Adversarial Probing](subsystems/biasscope.md) — §3.3, cost-bounded judge-API loop
- [WAXAL-NET Edge ASR](subsystems/waxal-net.md) — §3.4, training loop on MLX/ONNX-mobile lineage + Dart/Flutter field app
- [agent-airlock Hardening](subsystems/agent-airlock.md) — §3.5, adversarial git loop; the deliberate dependency exception
- [Compliance & Documentation](subsystems/compliance-loop.md) — §3.6, citation-currency loop

## Infrastructure (§4)

- [Isolation Tiers](infrastructure/isolation-tiers.md) — gVisor, Firecracker, Envoy credential injection
- [MCP Execution Boundary](infrastructure/mcp-execution-boundary.md) — runtime layer (four seams) + transport layer (JWS clearance)
- [Network Topology](infrastructure/network-topology.md) — Lagos/Nairobi/Cape Town realism for TTFT/throughput

## Strategy

- [Regulatory Landscape](strategy/regulatory-landscape.md) — AU Continental AI Strategy, Malabo Convention, Kenya ODPC, Nigeria NDPC, data sovereignty
- [Enterprise SaaS & VC](strategy/enterprise-saas.md) — tollbooth revenue model, Norrsken22 / Google AI Futures Fund alignment

## Build Plan (§5–7)

- [Phases](build-plan/phases.md) — Phase 0–5 with gates and acceptance criteria
- [Risk Register](build-plan/risk-register.md) — risks and mitigations beyond the platform caveat
- [Repository Layout](build-plan/repository-layout.md) — the ten planned repos

## Sources

- [Implementation Bible](sources/implementation-bible.md) — build spec, v1.0, source-of-truth for implementation
- [Implementation Research](sources/implementation-research.md) — the original architectural & strategic blueprint

**Page count: 30** · maintained on every ingest/lint per [AGENTS.md](AGENTS.md).
