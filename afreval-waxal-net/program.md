# §3.4 WAXAL-NET — agent operating instructions

Your job: minimize macro-averaged WER on the frozen WAXAL eval split — with
cross-domain OOD generalization tracked as a secondary metric — by fine-tuning
a compact ASR on the labeled train split, using the MLX/ONNX-mobile lineage.

## Setup

1. Read `README.md`, `configs/fine_tune.yaml`, and the frozen harness
   (`afreval-harness/harness/waxal_eval.py`).
2. Ensure the Stage B train split exists; if not, pull it:
   `afreval-harness/.venv/bin/python afreval-harness/scripts/acquire_waxal.py --splits train validation test`
3. Establish the baseline: `python eval_baseline.py --from-qa` → 0.4097 macro-WER.

## The loop (training-style)

1. Make ONE focused change to `configs/fine_tune.yaml` (model size, learning
   rate, LoRA rank, epochs, augmentation, language weighting).
2. `git commit` before running.
3. Run the fine-tune for a **fixed wall-clock budget** on the **target edge
   hardware class** (not a datacenter GPU). The device layer must assert the
   hardware class — a run claiming "beats zero-shot on low-end mobile" must
   fail loudly if it's actually on a workstation GPU.
4. Evaluate: `python eval_baseline.py --model <scorer>` → macro-WER + OOD.
5. Keep if macro-WER < 0.4097 (and OOD does not regress); revert otherwise.
6. Log every run.

## Rules

- **Never edit the harness or the eval split** — they are frozen.
- **CER is tracked alongside WER** — don't drop it (syllabary scripts reveal
  higher character-level accuracy).
- Report BOTH macro-WER and OOD — never cherry-pick in-distribution only.
- Export to ONNX/TFLite/CoreML for the field app; the edge artifact is the
  deliverable, not the training checkpoint.
- Keep going autonomously until stopped; log everything.
