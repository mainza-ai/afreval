#!/usr/bin/env python3
"""§3.1 N'Ko supplementary scoring — the third number (gap-analysis B1).

The pinned reference suite has zero N'Ko text, so the harness's nko premium
is always `nan`. This scores the ACTIVE candidate's N'Ko premium against a
SIB-200 N'Ko corpus (nqo_Nkoo) using the same frozen harness `evaluate()`
path — the corpus is supplementary (in-memory), the harness and its
segmentation/fertility math are untouched.

Usage (afri-fertility venv):
  ../afreval-harness/.venv/bin/python score_nko.py [--candidate EfficientRouteCandidate]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARNESS = HERE.parent / "afreval-harness"
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, str(HERE))

from candidates.tokenizer_candidate import EfficientRouteCandidate  # noqa: E402
from harness.tokenizer_eval import TokenizerEval, load_reference_suite  # noqa: E402


def load_nko_corpus(n: int = 204) -> dict[str, list[str]]:
    """SIB-200 nqo_Nkoo test sentences as a single-language corpus."""
    from datasets import load_dataset

    ds = load_dataset("Davlan/sib200", "nqo_Nkoo", split="test", trust_remote_code=False)
    return {"nqo": [row["text"] for row in ds.select(range(min(n, len(ds))))]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="EfficientRouteCandidate",
                    help="candidate class from candidates/tokenizer_candidate.py")
    ap.add_argument("--sentences", type=int, default=204)
    args = ap.parse_args()

    import importlib
    spec = importlib.import_module("candidates.tokenizer_candidate")
    cls = getattr(spec, args.candidate)
    tok = cls() if isinstance(cls, type) else cls

    suite = load_reference_suite()
    suite["nqo"] = load_nko_corpus(args.sentences)["nqo"]

    ev = TokenizerEval()
    result = ev.evaluate(tok, suite)

    row = next(r for r in result.languages if r.lang == "nqo")
    out = {
        "candidate": tok.id,
        "nqo_script_premium": round(result.script_premiums().get("nko"), 4),
        "nqo_fertility": round(row.fertility, 4),
        "nqo_premium_vs_eng": round(row.premium, 4) if row.premium is not None else None,
        "nqo_cpt": round(row.cpt, 4),
        "english_cpt": result.english_cpt,
        "corpus": f"SIB-200 nqo_Nkoo ({args.sentences} sentences, supplementary)",
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
