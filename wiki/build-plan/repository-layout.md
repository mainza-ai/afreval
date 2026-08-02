---
type: build-plan
tags: [repos, layout, architecture, monorepo]
updated: 2026-07-31
---

# Repository Layout

The **target** layout: eleven planned repos for the AfrEval implementation. The repos below are created as the phases in [phases.md](phases.md) are executed. **Implemented so far (in-tree):** `afreval-harness` (Phase 0 — **all three pins frozen**, WAXAL QA-approved at 72,145 clips), `afreval-context-score` (Phase 1 — deterministic Rust scorer, bit-identical), `afreval-tokenizer-research` (Phase 1 — §3.1 search loop, passing script-aware candidate), `afreval-airlock` (Phase 2 — four seams + JWS clearance + hardening loop, 19 tests, 0 bypasses), `afreval-biasscope` (§3.3), `afreval-compliance` (§3.6), `afreval-waxal-net` (Phase 4 — eval baseline 0.4097 macro-WER + loop scaffolding), `afreval-onprem` (Phase 5 prep — Tauri 2 skeleton embedding scorer + airlock), and `afreval-dashboard` (Phase 5 — cert + security web surface). Remaining stubs: `afreval-field-app` (Flutter, gates on WAXAL-NET) and `afreval-sdk` (gates on the certification API). Current workspace also contains `dev-docs/`, `wiki/`, and the three vendored substrate repos (`autoresearch/`, `AfroBench/` — with its `lm-evaluation-harness` submodule — and `afri-fertility/`), all flattened in-tree for re-engineering.

Each repo carries its own `program.md` (or `GOAL.md` where the fitness function isn't yet known — §3.2) as the literal, version-controlled instruction file for whichever agent runs that repo's loop. **These instruction files are the operational heart of the system** — treat changes to them with the same review rigor as changes to the scorer itself.

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
| `afreval-onprem` | Phase 5 — air-gapped certification + security dashboard client | Tauri 2 (Rust core) + TS/JS frontend | embeds `afreval-context-score` + `afreval-airlock` crates; Stronghold JWS vault; reuses `afreval-dashboard` frontend; local MCP server post-MVP ([report](../reports/tauri-integration.md)) |

## Related

- [Karpathy Loop](../concepts/karpathy-loop.md) — the program.md discipline
- [Phases](phases.md) — when each repo gets built
- [Synthesis](../synthesis.md) — open parameters affecting repo scopes
