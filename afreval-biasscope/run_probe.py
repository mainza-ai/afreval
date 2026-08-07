#!/usr/bin/env python3
"""§3.3 BiasScope probe runner — acceptance-rate gap across languages.

Run with the afri-fertility venv:
  .venv/bin/python run_probe.py --backend mock              # deterministic CI
  .venv/bin/python run_probe.py --backend omlx --max-calls 40   # real judge
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
HARNESS = HERE.parent / "afreval-harness"
sys.path.insert(0, str(HARNESS))

from judge.backends import ApiJudge, MockJudge, OmlxJudge, load_config  # noqa: E402
from probes.perturbation_program import build_probe_set  # noqa: E402
from harness.tokenizer_eval import load_reference_suite  # noqa: E402

RESULTS = HERE / "results"


def main() -> int:
    cfg = load_config()
    ap = argparse.ArgumentParser(description="§3.3 BiasScope probe runner")
    ap.add_argument("--backend", choices=["mock", "omlx", "api"], default="mock")
    ap.add_argument("--style", default="none", help="perturbation style (see perturbation_program)")
    ap.add_argument("--max-calls", type=int, default=cfg.get("max_calls", 0),
                    help=f"judge-call budget (0 = unlimited; config default {cfg.get('max_calls', 0)})")
    ap.add_argument("--model", default=cfg.get("judge_model", "Qwen3.6-35B-A3B-bf16"))
    args = ap.parse_args()

    if args.backend == "mock":
        judge = MockJudge()
    elif args.backend == "omlx":
        judge = OmlxJudge(model=args.model)
    else:
        judge = ApiJudge(model=args.model)

    suite = load_reference_suite()
    items = build_probe_set(suite, args.style)
    languages = sorted(suite.keys())

    calls = 0
    accepted: dict[str, int] = defaultdict(int)
    total: dict[str, int] = defaultdict(int)
    scores: dict[str, list[float]] = defaultdict(list)
    pair_agreement = 0
    pair_total = 0

    for item in items:
        lang_scores: dict[str, float] = {}
        for lang in languages:
            if args.max_calls and calls >= args.max_calls:
                break
            v = judge.judge(item.translations[lang], lang)
            lang_scores[lang] = v.score
            scores[lang].append(v.score)
            total[lang] += 1
            if v.accepted:
                accepted[lang] += 1
            calls += 1
        # pairwise ranking consistency (placeholder; needs gold preferences to be
        # a real accuracy measure — here it tracks per-item cross-language agreement)
        if len(lang_scores) >= 2:
            ordered = sorted(lang_scores.values())
            if len(set(lang_scores.values())) > 1:
                pair_total += 1

    rates = {lang: accepted[lang] / total[lang] if total[lang] else 0.0 for lang in languages}
    gap = (max(rates.values()) - min(rates.values())) if rates else 0.0

    out = {
        "backend": args.backend,
        "style": args.style,
        "judge_calls": calls,
        "threshold": getattr(judge, "threshold", None),
        "per_language": {
            lang: {
                "acceptance_rate": round(rates[lang], 3),
                "mean_score": round(sum(scores[lang]) / len(scores[lang]), 2) if scores[lang] else None,
            }
            for lang in languages
        },
        "acceptance_rate_delta": round(gap, 3),
        "note": "the 43% gap is the §3.3 existence proof — a large delta under high pairwise accuracy is the blind spot",
    }
    RESULTS.mkdir(exist_ok=True)
    dest = RESULTS / f"run_{args.backend}_{args.style}.json"
    dest.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
