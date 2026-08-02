#!/usr/bin/env python3
"""§3.4 WAXAL-NET eval — macro-averaged WER/CER over the frozen eval split.

Two modes:
  --from-qa   aggregate the existing QA pass 2 per-clip WER/CER (Sunbird /
              Ethio-ASR, WAXAL-tuned) into the zero-shot baseline. This is
              the baseline a fine-tuned edge model must beat.
  --model     evaluate a custom scorer (callable returning text per audio
              path) against the frozen QA-approved corpus. For fine-tuned
              models (when Stage B train data exists).

Metric (§3.4): macro-averaged WER over the 19-language WAXAL-NET set, with
CER tracked alongside and OOD-generalization as the secondary metric.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1] / "afreval-harness"
sys.path.insert(0, str(HARNESS))

from harness.waxal_eval import corpus_wer_cer, score_transcription  # noqa: E402

WAXAL = HARNESS / "data" / "waxal"


def load_frozen_corpus() -> list[dict]:
    """QA-approved (filtered) eval split manifests."""
    rows: list[dict] = []
    for man in sorted(WAXAL.glob("*_asr_filtered.jsonl")):
        for line in man.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def aggregate_qa_baseline() -> dict:
    per_lang: dict[str, list[float]] = defaultdict(list)
    for cfg in sorted(p.stem.removesuffix("_qa2") for p in WAXAL.glob("*_qa2.jsonl")):
        p = WAXAL / f"{cfg}_qa2.jsonl"
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            lang = r["language"].removesuffix("_asr")
            per_lang[lang].append(r["wer"])
    lang_means = {lang: sum(v) / len(v) for lang, v in per_lang.items()}
    macro = sum(lang_means.values()) / len(lang_means)
    return {
        "mode": "zero-shot baseline (Sunbird + Ethio-ASR via QA pass 2)",
        "languages": {lang: round(w, 4) for lang, w in sorted(lang_means.items())},
        "language_macro_wer": round(macro, 4),
        "n_languages": len(lang_means),
    }


def evaluate_model(scorer) -> dict:
    rows = load_frozen_corpus()
    by_lang: dict[str, list] = defaultdict(list)
    for r in rows:
        hyp = scorer(WAXAL / r["audio_path"])
        by_lang[r["language"]].append(score_transcription(r["transcription"], hyp))
    lang_wer = {lang: round(corpus_wer_cer(scores)[0], 4) for lang, scores in by_lang.items()}
    all_scores = [s for scores in by_lang.values() for s in scores]
    clip_wer, clip_cer = corpus_wer_cer(all_scores)
    return {
        "mode": "scorer evaluation",
        "languages": lang_wer,
        "clip_macro_wer": round(clip_wer, 4),
        "clip_macro_cer": round(clip_cer, 4),
        "n_clips": len(all_scores),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="§3.4 WAXAL-NET eval (macro WER/CER)")
    ap.add_argument("--from-qa", action="store_true", help="aggregate QA pass 2 -> zero-shot baseline")
    ap.add_argument("--out", default="baseline_results.json")
    args = ap.parse_args()

    if args.from_qa:
        result = aggregate_qa_baseline()
    else:
        from afri_fertility import load_tokenizer
        adapter = load_tokenizer("openai/o200k_base")  # placeholder scorer; real models later
        def scorer(path):
            return adapter.id  # not a real ASR — use --from-qa for the baseline
        result = evaluate_model(scorer)

    Path(args.out).write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
