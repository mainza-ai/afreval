---
type: build-plan
tags: [repos, layout, architecture, monorepo]
updated: 2026-08-03
---

# Repository Layout

The **target** layout: eleven planned repos for the AfrEval implementation. The repos below are created as the phases in [phases.md](phases.md) are executed. **All 11 repos are implemented in-tree:** `afreval-harness` (Phase 0 — **all three pins frozen**, WAXAL QA-approved at 72,145 clips), `afreval-context-score` (Phase 1 — deterministic Rust scorer, bit-identical), `afreval-tokenizer-research` (Phase 1 — §3.1 search loop, passing script-aware candidate, N'Ko measured 1.53), `afreval-airlock` (Phase 2 — four seams + JWS clearance + hardening loop, 25 tests, 31 variants, 0 bypasses, replay protection), `afreval-biasscope` (§3.3 — live judge run 2026-08-05 + bias-correction bridge), `afreval-compliance` (§3.6 — **100% citation current, 4/4**), `afreval-waxal-net` (Phase 4 — eval baseline 0.4097 macro-WER + loop scaffolding; Stage B train pull blocked on upstream HF Xet 404s), `afreval-field-app` (Phase 4 — Flutter scaffold, needs Flutter SDK to build), `afreval-sdk` (Phase 5 — Python working + packaged, TypeScript buildable + tested), `afreval-onprem` (Phase 5 prep — Tauri 2 skeleton embedding scorer + airlock, trust-root vault fails closed), and `afreval-dashboard` (Phase 5 — cert + security web surface), `afreval-api` (Phase C — the certification HTTP API: `/v1/certify` + `/v1/security` + `/v1/compliance`, the tollbooth surface), and `afreval-envoy` (Phase E — Envoy credential-injection sidecar, docker-compose verified). **CI (`.github/workflows/ci.yml`) runs all test suites + the §3.5 hardening loop + certification determinism check on push.** Current workspace also contains `dev-docs/`, `wiki/`, and the three vendored substrate repos (`autoresearch/`, `AfroBench/` — with its `lm-evaluation-harness` submodule — and `afri-fertility/`), all flattened in-tree for re-engineering.

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
