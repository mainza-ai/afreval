---
type: subsystem
tags: [context-score, calibration, certification, rust, GOAL.md, §3.2]
updated: 2026-07-31
---

# Subsystem §3.2 — Context Score Calibration Loop

Tunes the weighting function of the [Context Score](../concepts/context-score.md) — AfrEval's core IP. The weights are per-industry (`weights/{vertical}.yaml` — telco weights fluidity/latency, bank weights security/alignment) and are today presumably hand-set. **That's a search problem.**

| Field | Spec |
|---|---|
| **Frozen harness** | The three scoring pipelines from §2 — WAXAL WER, AfroBench-LITE, afri-fertility — deterministic and version-pinned |
| **Mutable artifact** | `weights/{vertical}.yaml` — the weight function + threshold per industry vertical |
| **Instruction file** | `GOAL.md` (the [jmilinovich/goal-md](https://github.com/webfuse-com/awesome-autoresearch) pattern) — **because the fitness function itself isn't fully known yet** |
| **Metric** | Precision/recall of the weight function against incident-labeled deployment history, or a synthetic adversarial holdout if real incident data is too sparse in early operation |
| **Budget** | `git commit`/revert per weight-config change; N = fixed iterations per calibration run, not wall-clock |
| **Loop flavor** | `git commit`/revert style (generalized Karpathy Loop) |
| **Language** | Rust for the production scorer (same hot path as the zero-trust runtime); Python for the search loop calling the Rust scorer over thin FFI/gRPC |
| **Repo** | `afreval-context-score` (Rust core + `research/` Python search harness) |
| **Cadence** | Re-run **at minimum monthly per vertical**, and immediately on any upstream frontier-model release relevant to a currently-certified deployment (a model passing in January can drift into non-compliance by March) |

## The GOAL.md discipline (two-pass, don't skip pass one)

Unlike §3.1, the fitness function isn't known yet. Do **not** jump straight to weight search:

1. **First loop pass:** construct the labeled-outcome dataset — models that passed certification and later caused incidents vs. models that held up in production.
2. **Second loop pass:** search weights against that dataset.

This is precisely the mistake the goal-md pattern exists to prevent.

## §3.2.1 Certification loop vs. calibration loop — kept structurally separate

- **Calibration loop** (this page) tunes *how* scores are weighted. It is a search loop.
- **Certification loop** is the actual per-model, per-deployment scoring pass against a submitted model. It is **not a search loop** — a deterministic pipeline invocation that must be reproducible and auditable: *same model + same weight config + same harness version → same score, always.*
- Do **not** let an agent "optimize" the certification pipeline against throughput without an explicit accuracy-preserving constraint — that would silently recreate the [LLM-as-judge bias](../concepts/llm-as-judge-bias.md) failure mode inside AfrEval's own scorer.
- The Phase 1 deliverable is the deterministic scorer first; the calibration loop is Phase 3.

## Related

- [Context Score](../concepts/context-score.md) — the artifact being calibrated
- [Karpathy Loop](../concepts/karpathy-loop.md) — GOAL.md pattern, loop flavor
- [AfroBench](../substrates/afrobench.md) / [WAXAL](../substrates/waxal.md) / [afri-fertility](../substrates/afri-fertility.md) — the frozen pipelines
- [Risk register — proxy-metric optimization](../build-plan/risk-register.md)
- [Phases — Phase 1 & 3](../build-plan/phases.md)
