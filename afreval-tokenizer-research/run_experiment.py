#!/usr/bin/env python3
"""§3.1 experiment runner — deterministic scoring of the active candidate.

Scores the candidate in candidates/tokenizer_candidate.py against the frozen
§3.1 harness (afreval-harness/harness/tokenizer_eval.py) on the pinned
reference suite, applies the §3.1 rules vs baseline.json, and logs to
results.tsv.

Run with the afri-fertility venv:
  afreval-harness/.venv/bin/python run_experiment.py [--baseline] [--candidate <id>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARNESS = HERE.parent / "afreval-harness"
sys.path.insert(0, str(HARNESS))

from harness.tokenizer_eval import (  # noqa: E402
    ETHIOPIC,
    LATIN,
    NKO,
    TokenizerEval,
    english_cpt_regression,
    load_reference_suite,
)

BASELINE_FILE = HERE / "baseline.json"
RESULTS_FILE = HERE / "results.tsv"
MAX_ENGLISH_CPT_REGRESSION_PCT = 5.0


def load_candidate(candidate_id: str | None):
    spec = importlib_import("candidates.tokenizer_candidate")
    if candidate_id:
        cls = getattr(spec, candidate_id)
        return cls() if isinstance(cls, type) else cls
    return spec.ACTIVE_CANDIDATE() if isinstance(spec.ACTIVE_CANDIDATE, type) else spec.ACTIVE_CANDIDATE


def importlib_import(name):
    import importlib
    sys.path.insert(0, str(HERE))
    return importlib.import_module(name)


def main() -> int:
    ap = argparse.ArgumentParser(description="§3.1 tokenizer experiment runner")
    ap.add_argument("--baseline", action="store_true", help="record the o200k_base baseline")
    ap.add_argument("--candidate", help="candidate class name (default: ACTIVE_CANDIDATE)")
    args = ap.parse_args()

    suite = load_reference_suite()
    ev = TokenizerEval()

    if args.baseline:
        from afri_fertility import load_tokenizer
        base = ev.evaluate(load_tokenizer("openai/o200k_base"), suite)
        data = {
            "tokenizer": base.tokenizer,
            "english_cpt": base.english_cpt,
            "script_premiums": {s: v for s, v in base.script_premiums().items() if v is not None},
        }
        BASELINE_FILE.write_text(json.dumps(data, indent=2))
        print(f"baseline written -> {BASELINE_FILE}")
        print(f"  english_cpt={data['english_cpt']:.4f} script_premiums={ {k: round(v,4) for k,v in data['script_premiums'].items()} }")
        return 0

    if not BASELINE_FILE.exists():
        print("no baseline.json; run with --baseline first", file=sys.stderr)
        return 2

    baseline = json.loads(BASELINE_FILE.read_text())
    candidate = load_candidate(args.candidate)
    result = ev.evaluate(candidate, suite)

    p = result.script_premiums()
    b = baseline["script_premiums"]
    cpt_ok = english_cpt_regression(result.english_cpt, baseline["english_cpt"], MAX_ENGLISH_CPT_REGRESSION_PCT)

    def _ok(script):
        v = p.get(script)
        if v is None:
            return True  # no data for this script in the corpus: not a regression
        return v <= b.get(script, float("inf"))

    if not cpt_ok:
        status = "FAIL_CPT_REGRESSION"
    elif not (_ok(LATIN) and _ok(ETHIOPIC) and _ok(NKO)):
        status = "FAIL_SCRIPT_REGRESSION"
    else:
        status = "PASS"

    row = "\t".join([
        "HEAD", getattr(candidate, "id", "candidate"),
        f"{p.get(LATIN) or float('nan'):.4f}", f"{p.get(ETHIOPIC) or float('nan'):.4f}",
        f"{p.get(NKO) or float('nan'):.4f}", f"{result.english_cpt:.4f}",
        status, "",
    ])
    if not RESULTS_FILE.exists():
        RESULTS_FILE.write_text("commit\tcandidate_id\tlatin_premium\tethiopic_premium\tnko_premium\tenglish_cpt\tstatus\tnote\n")
    with open(RESULTS_FILE, "a") as f:
        f.write(row + "\n")

    print(f"candidate: {getattr(candidate, 'id', 'candidate')}")
    print(f"  script premiums: latin={p.get(LATIN)} ethiopic={p.get(ETHIOPIC)} nko={p.get(NKO)}")
    print(f"  english_cpt: {result.english_cpt:.4f} (baseline {baseline['english_cpt']:.4f})")
    print(f"  verdict: {status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
