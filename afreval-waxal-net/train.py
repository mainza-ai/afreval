#!/usr/bin/env python3
"""§3.4 WAXAL-NET fine-tuning entry point (training-style loop).

Placeholder until Stage B (labeled train split) is acquired — see README.
The device layer asserts the target hardware class before any run; a claim
of "beats zero-shot on low-end mobile" fails loudly if hardware mismatches.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1] / "afreval-harness"
sys.path.insert(0, str(HARNESS))


def main() -> int:
    ap = argparse.ArgumentParser(description="§3.4 WAXAL-NET fine-tune")
    ap.add_argument("--config", default=str(Path(__file__).parent / "configs" / "fine_tune.yaml"))
    ap.add_argument("--budget-min", type=float, default=5.0, help="fixed wall-clock budget (minutes)")
    args = ap.parse_args()

    train_dir = HARNESS / "data" / "waxal" / "raw"
    if not train_dir.exists() or not any(train_dir.glob("data/ASR/*/*-train-*")):
        print("Stage B train split not acquired. Run:", file=sys.stderr)
        print("  python afreval-harness/scripts/acquire_waxal.py --splits train validation test", file=sys.stderr)
        return 2

    print(f"fine-tune entry ready (config={args.config}, budget={args.budget_min} min)")
    print("TODO: wire the MLX fine-tune (base model + LoRA) once the train substrate is present.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
