---
type: build-plan
tags: [repos, layout, architecture, monorepo]
updated: 2026-07-31
---

# Repository Layout

Ten planned repos. Each carries its own `program.md` (or `GOAL.md` where the fitness function isn't yet known — §3.2) as the literal, version-controlled instruction file for whichever agent runs that repo's loop. **These instruction files are the operational heart of the system** — treat changes to them with the same review rigor as changes to the scorer itself.

| Repo | Subsystem / phase | Language | Notes |
|---|---|---|---|
| `afreval-harness` | Phase 0 — frozen WAXAL/AfroBench/afri-fertility pins | Python + data | checksummed, read-only harness; the device layer from §1.3 lives here too |
| `afreval-tokenizer-research` | §3.1 — tokenizer & vocab search | Python | training-style loop |
| `afreval-context-score` | §3.2 — Context Score | Rust core + Python `research/` | Rust scorer shares hot path with zero-trust runtime; FFI/gRPC boundary |
| `afreval-biasscope` | §3.3 — BiasScope probing | Python + optional Rust | cost-bounded judge-API loop |
| `afreval-waxal-net` | §3.4 — edge ASR fine-tuning | Python | MLX/ONNX-mobile lineage |
| `afreval-field-app` | §3.4 — field data collection | Dart/Flutter | image-prompted elicitation UI + on-device eval telemetry |
| `afreval-airlock` | §3.5 — execution boundary | Rust core + TS/JS orchestration | vendored/extended fork of `sattyamjjain/agent-airlock` (license-checked) |
| `afreval-compliance` | §3.6 — citation-currency loop | Python/Markdown | |
| `afreval-dashboard` | Phase 5 — enterprise SaaS surface | TypeScript/JavaScript | security dashboard + enterprise integrations |
| `afreval-sdk` | Phase 5 — client SDKs | TypeScript/JavaScript + Python | |

## Related

- [Karpathy Loop](../concepts/karpathy-loop.md) — the program.md discipline
- [Phases](phases.md) — when each repo gets built
- [Synthesis](../synthesis.md) — open parameters affecting repo scopes
