---
type: concept
tags: [karpathy-loop, autoresearch, design-pattern, autonomous-research]
updated: 2026-07-31
---

# Karpathy Loop

The core design pattern underlying the entire AfrEval system. Named after [karpathy/autoresearch](https://github.com/karpathy/autoresearch): "give an AI agent a small but real LLM training setup and let it experiment autonomously overnight."

## The canonical pattern (three files + a rule)

- **`prepare.py`** — a frozen, human-owned harness. Data prep, eval protocol, runtime utilities. **The agent never touches this.**
- **`train.py`** — the single mutable artifact. The agent rewrites architecture, hyperparameters, optimizer — anything — inside this one file.
- **`program.md`** — the agent's operating instructions, written and edited by the human, read by the agent.

The loop: modify → run for a **fixed time budget** (5 minutes wall-clock in the original) → score against **one scalar metric** (`val_bpb`, vocab-size-independent bits-per-byte) → keep if improved, discard if not → repeat. At ~12 experiments/hour this yields ~100 experiments overnight, unattended.

Formalized (per the [awesome-autoresearch](https://github.com/webfuse-com/awesome-autoresearch) index):

```
AGENT + CONSTRAINED_SCOPE + SCALAR_METRIC + FAST_VERIFICATION = AUTONOMOUS_IMPROVEMENT
```

The canonical repo lives locally at `../autoresearch/` (clone of karpathy/autoresearch: `prepare.py`, `train.py`, `program.md`, plus analysis tooling).

## The generalized loop

[uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) ("Claude Autoresearch") generalizes the exact loop to **any domain with a measurable metric** — code, security, docs, DevOps — using `git commit → verify → keep/revert` instead of a training run:

```
LOOP (N iterations or until done):
  1. Review current state + git history + results log
  2. Pick the next change (based on what worked, what failed, what's untried)
  3. Make ONE focused change
  4. Git commit (before verification)
  5. Run mechanical verification (tests, benchmarks, scores)
  6. If improved → keep. If worse → git revert. If crashed → fix or skip.
  7. Log the result
  8. Repeat
```

> **Load-bearing insight for AfrEval:** *not every subsystem is an ML training loop, but every subsystem can be a Karpathy Loop.* Tokenizer search is training-style. Adversarial red-teaming and weight calibration are `git commit`/revert-style. The loop flavor is specified per subsystem — see [Tokenizer search](../subsystems/tokenizer-search.md) through [Compliance](../subsystems/compliance-loop.md).

`uditgoenka/autoresearch` is **reference-only, not a base repo** — it's markdown with no domain logic underneath. Read it once for how it structures a routing file + per-command instruction files, then write AfrEval's own `program.md`/`GOAL.md` per subsystem.

Related forks worth reading as technique references (not dependencies): leo-lilinxiao/codex-autoresearch (Codex-native, resume, lessons-across-runs), SeeleAI/Thoth (dashboard-first, durable runs, reviewable verdicts — relevant to the audit-trail requirement), jmilinovich/goal-md (`GOAL.md` pattern for constructing a fitness function *before* optimizing — used in §3.2).

## The platform caveat — resolved by re-engineering, not forking

The base repo is **single NVIDIA GPU only**; the maintainer has deferred platform generalization to forks. This is a first-class constraint for AfrEval, whose entire thesis is performance under constrained compute.

**Resolution:** clone the base repo once, then re-engineer the device layer until the CUDA ceiling is gone. AfrEval takes **zero runtime or code dependency** on any third-party fork — the forks are technique references (read their diffs for how they solved a constraint, re-implement the technique yourself). Re-engineering task list (in `afreval-harness/`):

1. Strip the hard CUDA/FlashAttention-3 assumption.
2. Add device detection — CUDA → MPS → CPU/ONNX-mobile, mirroring nanochat's autodetection and Milimo Quantum's HAL (Aer CPU sim, PyTorch MPS, MLX primary inference).
3. Gate SDPA fallback and MPS batch/memory handling behind the device layer so the same artifact runs unmodified anywhere.
4. For the [WAXAL-NET loop](../subsystems/waxal-net.md): support an **explicit hardware-class assertion** — a run claiming "beats zero-shot on low-end mobile" must fail loudly if it's actually running on a workstation GPU.
5. Non-ML loops (Context Score calibration, BiasScope, agent-airlock) need **no device layer** — they're git/revert loops, built directly.

## How the loop flavors map to AfrEval's subsystems

| Subsystem | Loop flavor | Metric |
|---|---|---|
| [Tokenizer search](../subsystems/tokenizer-search.md) | Training-style | Script-stratified mean fertility premium |
| [Context Score calibration](../subsystems/context-score-calibration.md) | git commit/revert (GOAL.md) | Precision/recall vs. incident history |
| [BiasScope probing](../subsystems/biasscope.md) | git commit/revert, cost-budgeted | Acceptance-rate delta across languages |
| [WAXAL-NET edge ASR](../subsystems/waxal-net.md) | Training-style, MLX/ONNX lineage | Macro-averaged WER (19 languages) + OOD |
| [agent-airlock hardening](../subsystems/agent-airlock.md) | git commit/revert, adversarial | Bypass rate per seam |
| [Compliance](../subsystems/compliance-loop.md) | git commit/revert | Citation-currency check |

## Related

- [African Language Tax](african-language-tax.md) — the phenomenon the tokenizer loop optimizes against
- [Context Score](context-score.md) — what the calibration loop tunes
- [Zero-Trust Sandboxing](zero-trust-sandboxing.md) — what the agent-airlock loop hardens
- [Build Plan — Phases](../build-plan/phases.md) — when the loops go live (Phase 3)
