# afreval-context-score

Deterministic **Context Score** scorer for Milimo AfrEval (§3.2). Rust core, shipped in Phase 1 as an invocable, auditable pipeline — **before** the autonomous calibration loop exists (that is Phase 3, in `research/`).

The scorer is model-agnostic: it takes a model evaluation report (from the three frozen harnesses) and a per-vertical weight config, and produces a 0–100 Context Score.

## The score

```
Context Score = w_LF·LinguisticFidelity + w_CS·CulturalSafety + w_SE·StructuralEconomics   (Σw = 1, per vertical)

LinguisticFidelity = w_a·(100·(1−WAXAL_macro_WER)) + w_t·(100·AfroBenchLITE_acc)
CulturalSafety     = bias-corrected judge score            (BiasScope pipeline, §3.3 — input for Phase 1)
StructuralEconomics = 100 / mean_fertility_premium         (inverse of the African Language Tax)
pass               = Context Score ≥ vertical threshold
```

Only `+ − · / min max` — no transcendentals — so output is **bit-identical on repeated runs** (Phase 1 acceptance criterion; verified by test + CLI `cmp`).

## CLI

```bash
# score a model report against a vertical's frozen weights
afreval-context-score score --report examples/report.example.json --weights weights/telco.yaml
# exit 0 = pass, 1 = below threshold, 2 = invalid input

# validate report + weights without scoring
afreval-context-score validate --report ... --weights ...
```

## Layout

```
src/report.rs   # model evaluation report (harness results) + validation
src/config.rs   # per-vertical weights YAML + validation (Σ weights = 1 enforced)
src/score.rs    # deterministic scoring pipeline
src/main.rs     # CLI
weights/        # telco.yaml, banking.yaml — per-industry weights (mutable per §3.2)
examples/       # sample model report
research/       # Phase 3 Python calibration search loop (placeholder — fitness function first, per GOAL.md)
tests/          # determinism + known-value + validation tests
```

## Conventions

- **Report + weights must validate or the scorer errors loudly** (no silent defaulting) — auditability requirement.
- **Weight configs are the mutable artifact** of the §3.2 calibration loop; the scorer code is frozen.
- **Certification vs calibration stay separate** (§3.2.1): this binary is the deterministic certification path. Never "optimize" it against throughput.
- Output is stable JSON (sorted keys, fixed field order) — byte-comparable across runs.

## Related

- [Context Score concept](../wiki/concepts/context-score.md)
- [§3.2 calibration subsystem](../wiki/subsystems/context-score-calibration.md)
- [Phase 1 acceptance](../wiki/build-plan/phases.md): bit-identical repeated runs ✓
