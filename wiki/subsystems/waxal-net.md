---
type: subsystem
tags: [waxal-net, asr, edge, fine-tuning, mlx, onnx, §3.4]
updated: 2026-07-31
---

# Subsystem §3.4 — WAXAL-NET Edge ASR Fine-Tuning Loop

The clearest 1:1 reuse of the original autoresearch training-loop shape — and the place where the [platform caveat resolution](../concepts/karpathy-loop.md) (MLX/ONNX-mobile lineage, not CUDA) is **non-optional**.

| Field | Spec |
|---|---|
| **Frozen harness** | WAXAL held-out eval split; WER/CER scoring — **CER tracked alongside WER** (for syllabary-script languages the CER/WER ratio reveals meaningfully higher character-level accuracy than WER alone suggests) |
| **Mutable artifact** | ASR fine-tune config/architecture — same "one file, agent edits it" discipline as `train.py` |
| **Instruction file** | `program.md`, adapted from the MLX/edge fork lineage, not the CUDA original |
| **Metric** | Macro-averaged **WER across the 19-language WAXAL-NET set**, with cross-domain **OOD generalization tracked as a secondary metric** — per the WAXAL-NET paper: fine-tuned models generalize better OOD; zero-shot models only win in-distribution. You want both numbers, or you'll ship a model that's great on the benchmark and brittle in the field. |
| **Budget** | Fixed wall-clock per fine-tune run, **sized for the target edge hardware class, not a datacenter GPU** — if you're validating "runs on low-end mobile," the search loop must run on comparable compute or the result is meaningless |
| **Loop flavor** | Training-style, MLX/ONNX-mobile fork lineage |
| **Language** | Python for training/search; export to ONNX/TFLite/Core ML for on-device; Dart/Flutter client for field data collection (image-prompted elicitation UI, matching WAXAL's own collection methodology) and on-device eval telemetry |
| **Repos** | `afreval-waxal-net` (Python core) + `afreval-field-app` (Dart/Flutter) |

## Target baseline to beat

Fine-tuned compact edge models reached **38.0% macro-WER vs 64.9%** for massively multilingual zero-shot foundation models on spontaneous African speech ([WAXAL](../substrates/waxal.md)). This is the benchmark to beat, not just cite.

## Hardware-class assertion (device layer task #4)

The device layer must support an **explicit hardware-class assertion**, not silent autodetection-and-proceed. If a run claims to validate "beats zero-shot on low-end mobile WER," it must **fail loudly** if it detects it's actually running on a workstation GPU — auto-fallback would silently invalidate exactly the claim Phase 4's acceptance criteria depend on.

## Related

- [WAXAL substrate](../substrates/waxal.md) — data, methodology, and the WAXAL-NET result
- [Karpathy Loop — platform caveat](../concepts/karpathy-loop.md)
- [Phases — Phase 4](../build-plan/phases.md) — acceptance criteria require target-class hardware
- [Risk register — hardware transfer](../build-plan/risk-register.md)
