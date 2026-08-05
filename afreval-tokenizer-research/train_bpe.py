#!/usr/bin/env python3
"""Train a BPE candidate on a mixed English + African-language corpus.

Corpus: the pinned reference suite + a sample of the WAXAL eval transcriptions
(19 African languages) + optional SIB-200 African-Latin text (the §2.3-pinned
corpus that closes the Yoruba/Hausa/Igbo/Swahili gap — those four are WAXAL
TTS-only, so without SIB-200 the BPE never sees African-Latin script text).
The trained candidate is saved to candidates/trained_bpe.json and evaluated by
run_experiment.py --candidate TrainedBPE.

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

# SIB-200 covers the African-Latin languages that the WAXAL reference suite
# lacks in usable volume (yor/hau/ibo/swh are WAXAL TTS-only). The reference
# suite's own SIB-200/flores codes come from the pinned language registry.
_SIB200_AFRICAN_LATIN = ["yor_Latn", "hau_Latn", "ibo_Latn", "swh_Latn", "lin_Latn", "lug_Latn"]


def waxal_transcriptions(sample: int, seed: int) -> list[str]:
    waxal = HARNESS / "data" / "waxal"
    texts: list[str] = []
    if waxal.exists():
        for man in sorted(waxal.glob("*_asr.jsonl")):
            for line in list(man.open(encoding="utf-8"))[:200]:
                texts.append(json.loads(line)["transcription"])
    rng = random.Random(seed)
    return rng.sample(texts, min(sample, len(texts)))


def sib200_african_latin(sample_per_lang: int, seed: int) -> list[str]:
    """SIB-200 test-split sentences for the African-Latin languages.

    This is the §3.1 corpus-mix lever that the search loop lacks today. Falls
    back to the reference suite's own text for a language if the Hub dataset
    is unreachable (so a network blip never breaks training).
    """
    texts: list[str] = []
    rng = random.Random(seed)
    try:
        from datasets import load_dataset
    except ImportError:
        print("datasets not installed — skipping SIB-200 corpus")
        return []
    for code in _SIB200_AFRICAN_LATIN:
        try:
            for split in ("test", "train"):
                ds = load_dataset("Davlan/sib200", code, split=split, trust_remote_code=False)
                texts.extend(rng.sample([row["text"] for row in ds], min(sample_per_lang, len(ds))))
        except Exception as e:
            print(f"SIB-200 {code} unavailable: {e}")
    return texts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--merges", type=int, default=500)
    ap.add_argument("--sample", type=int, default=2000, help="WAXAL transcriptions to sample")
    ap.add_argument("--sib200-per-lang", type=int, default=0,
                    help="per-language SIB-200 African-Latin sentences to add (0 = off)")
    ap.add_argument("--id", default="candidate/bpe-v0")
    args = ap.parse_args()

    suite = load_reference_suite()
    words = [w for texts in suite.values() for s in texts for w in s.split()]
    words += [w for s in waxal_transcriptions(args.sample, 7) for w in s.split()]
    if args.sib200_per_lang:
        sib = sib200_african_latin(args.sib200_per_lang, 7)
        words += [w for s in sib for w in s.split()]
        print(f"SIB-200 African-Latin added: {len(sib)} sentences")
    print(f"corpus: {len(words)} words from reference suite + WAXAL sample" +
          (" + SIB-200" if args.sib200_per_lang else ""))

    merges = train_bpe(words, args.merges)
    OUT.write_text(json.dumps({"id": args.id, "merges": merges}))
    print(f"trained {len(merges)} merges -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
