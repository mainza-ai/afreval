# afreval-waxal-net

§3.4 edge ASR fine-tuning loop. The clearest 1:1 reuse of the original
autoresearch training-loop shape — **training-style, MLX/ONNX-mobile lineage
(not CUDA)**. Target: a fine-tuned compact edge model beats zero-shot
foundation models on macro-averaged WER over the frozen WAXAL eval split,
run on hardware comparable to the actual target device class.

## Loop contract (§3.4)

| Field | Value |
|---|---|
| Frozen harness | WAXAL held-out eval split (QA-approved: `afreval-harness/data/waxal/*_asr_filtered.jsonl`), WER **+ CER** |
| Mutable artifact | `configs/fine_tune.yaml` (the ASR fine-tune config/architecture) |
| Instruction file | `program.md` |
| Metric | **macro-averaged WER** over the frozen eval set, with **OOD generalization** as the secondary metric |
| Budget | fixed wall-clock per fine-tune run, sized for the **target edge hardware class** |
| Loop flavor | training-style, MLX/ONNX-mobile |
| Languages | Python (train/eval) → ONNX/TFLite/CoreML export; `afreval-field-app` (Dart/Flutter) for collection |

## Baseline (zero-shot — the number to beat)

`eval_baseline.py --from-qa` aggregates QA pass 2 (Sunbird + Ethio-ASR,
WAXAL-aware) into the baseline:

**language-macro WER = 0.4097** (18 languages; lug 0.21 best, kpo 0.80 worst).
A fine-tuned edge model must beat this on comparable hardware.

## Status

- **Stage A (Phase 0):** eval split frozen (72,145 clips / 18 languages) — done.
- **Stage B (Phase 4):** labeled **train** split acquisition is pending
  (`afreval-harness/scripts/acquire_waxal.py --splits train validation test`).
  `train.py` is the loop entry point; fine-tuning runs once the train substrate
  is available.

## Related

- [WAXAL-NET subsystem](../wiki/subsystems/waxal-net.md)
- [WAXAL substrate](../wiki/substrates/waxal.md)
- [Platform caveat resolution](../wiki/concepts/karpathy-loop.md)
