#!/usr/bin/env python3
"""Train a BPE candidate on a mixed English + African-language corpus.

Corpus: the pinned reference suite + a sample of the WAXAL eval transcriptions
(19 African languages). The trained candidate is saved to
candidates/trained_bpe.json and evaluated by run_experiment.py --candidate TrainedBPE.

The §3.1 constraint is deliberately stringent: English CPT must not regress
more than 5% vs o200k_base (5.73). A from-scratch multilingual BPE will
struggle there — that is the real search problem the loop exists to solve.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARNESS = HERE.parent / "afreval-harness"
sys.path.insert(0, str(HARNESS))

from candidates.bpe_trainer import train_bpe  # noqa: E402
from harness.tokenizer_eval import load_reference_suite  # noqa: E402

OUT = HERE / "candidates" / "trained_bpe.json"


def waxal_transcriptions(sample: int, seed: int) -> list[str]:
    waxal = HARNESS / "data" / "waxal"
    texts: list[str] = []
    if waxal.exists():
        for man in sorted(waxal.glob("*_asr.jsonl")):
            for line in list(man.open(encoding="utf-8"))[:200]:
                texts.append(json.loads(line)["transcription"])
    rng = random.Random(seed)
    return rng.sample(texts, min(sample, len(texts)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--merges", type=int, default=500)
    ap.add_argument("--sample", type=int, default=2000, help="WAXAL transcriptions to sample")
    ap.add_argument("--id", default="candidate/bpe-v0")
    args = ap.parse_args()

    suite = load_reference_suite()
    words = [w for texts in suite.values() for s in texts for w in s.split()]
    words += [w for s in waxal_transcriptions(args.sample, 7) for w in s.split()]
    print(f"corpus: {len(words)} words from reference suite + WAXAL sample")

    merges = train_bpe(words, args.merges)
    OUT.write_text(json.dumps({"id": args.id, "merges": merges}))
    print(f"trained {len(merges)} merges -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
