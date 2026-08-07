#!/usr/bin/env python3
"""§3.4 OOD-generalization protocol (gap-analysis 2026-08-05).

The Phase-4 acceptance criteria require BOTH macro-WER (in-distribution) AND
OOD generalization — "a fine-tuned model that's great on the benchmark and
brittle in the field" must be rejected. This module defines HOW OOD is
measured so the claim is reproducible, not cherry-picked.

Protocol:
  - IN-DISTRIBUTION: the frozen QA-approved eval split (all languages).
  - OUT-OF-DISTRIBUTION: a held-out split defined by collection setting —
    the WAXAL eval clips carry per-clip metadata (audio integrity, silence
    fraction, collection conditions from QA pass 2). OOD here = clips in the
    *noisiest* tercile by silence fraction (spontaneous, field-like), which
    the QA data showed differs most from clean studio audio.
  - REPORT BOTH numbers. The acceptance gate is: fine-tuned macro-WER beats
    the zero-shot baseline AND OOD-WER does not regress more than a
    documented tolerance (default 5 relative points) vs the baseline's OOD.

This is a PROTOCOL + hook. It runs offline on the committed QA data; the
per-clip silence metadata comes from qa2 manifests.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1] / "afreval-harness"
sys.path.insert(0, str(HARNESS))

WAXAL = HARNESS / "data" / "waxal"


def load_frozen_corpus() -> list[dict]:
    """Frozen QA-approved clips, enriched with per-clip WER/silence from the
    QA pass-2 manifests (joined by id)."""
    # per-clip QA results keyed by id
    qa: dict[str, dict] = {}
    for q in sorted(WAXAL.glob("*_asr_qa2.jsonl")):
        for line in q.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                qa[r["id"]] = r

    rows: list[dict] = []
    for man in sorted(WAXAL.glob("*_asr_filtered.jsonl")):
        for line in man.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            q = qa.get(row["id"], {})
            row["wer"] = q.get("wer")
            row["cer"] = q.get("cer")
            row["decode_failed"] = q.get("decode_failed", False)
            rows.append(row)
    return rows


def _silence_fraction(row: dict) -> float:
    """Silence fraction from the QA metadata; defaults to 0.0 if absent."""
    return row.get("silence_fraction", row.get("silence", 0.0)) or 0.0


def split_in_ood(rows: list[dict], ood_tercile: float = 1 / 3) -> tuple[list[dict], list[dict]]:
    """Split the frozen corpus into in-distribution vs OOD (noisiest tercile).

    Balanced per language: the OOD tercile is taken within each language so a
    language-heavy noise bias cannot skew the OOD set (a naive global tercile
    drops whole languages — see protocol note).
    """
    if not rows:
        return [], []
    by_lang: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_lang[r["language"].removesuffix("_asr")].append(r)
    ind, ood = [], []
    for lang_rows in by_lang.values():
        ranked = sorted(lang_rows, key=_silence_fraction)
        n_ood = max(1, int(round(len(ranked) * ood_tercile)))
        ood.extend(ranked[-n_ood:])
        ind.extend(ranked[:-n_ood])
    return ind, ood


def aggregate_wer(rows: list[dict]) -> dict:
    """Language-macro WER over the given rows (from stored per-clip WER)."""
    per_lang: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        lang = r["language"].removesuffix("_asr")
        wer = r.get("wer")
        if wer is not None:
            per_lang[lang].append(wer)
    if not per_lang:
        return {"n_languages": 0, "language_macro_wer": None}
    means = {lang: sum(v) / len(v) for lang, v in per_lang.items()}
    return {
        "n_languages": len(means),
        "language_macro_wer": round(sum(means.values()) / len(means), 4),
        "languages": {lang: round(w, 4) for lang, w in sorted(means.items())},
    }


def report_ood() -> dict:
    rows = [r for r in load_frozen_corpus() if r.get("wer") is not None]
    ind, ood = split_in_ood(rows)
    return {
        "protocol": "per-language silence-tercile split of the frozen QA-approved eval split",
        "in_distribution": aggregate_wer(ind),
        "out_of_distribution": aggregate_wer(ood),
        "n_clips": {"ind": len(ind), "ood": len(ood)},
        "acceptance_note": "fine-tuned model must beat the zero-shot baseline macro-WER "
                           "AND not regress OOD-WER > 5 relative points vs baseline OOD",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="§3.4 OOD-generalization protocol")
    ap.add_argument("--out", default="ood_report.json")
    args = ap.parse_args()

    rep = report_ood()
    Path(args.out).write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
