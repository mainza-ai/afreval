#!/usr/bin/env python3
"""End-to-end Phase 0 -> Phase 1 demo.

Runs the frozen §3.1 tokenizer harness against the pinned reference suite with
a real tokenizer (o200k_base), builds a Context Score ModelReport, and scores
it with the Rust scorer.

Run from the harness venv (has afri-fertility):
  afreval-harness/.venv/bin/python afreval-context-score/examples/score_from_harness.py
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "afreval-harness"))

from harness.report import report_from_eval  # noqa: E402
from harness.tokenizer_eval import TokenizerEval, load_reference_suite  # noqa: E402

SCORER = HERE.parent / "target" / "release" / "afreval-context-score"
WEIGHTS = HERE.parent / "weights" / "telco.yaml"


def main() -> int:
    from afri_fertility import load_tokenizer

    suite = load_reference_suite()
    result = TokenizerEval().evaluate(load_tokenizer("openai/o200k_base"), suite)

    report = report_from_eval(
        "o200k_base-demo",
        result,
        waxal_macro_wer=0.38,
        afrobench_lite_accuracy=0.62,
        bias_corrected_judge_score=78.0,
        pins={
            "afri_fertility_pin": "0.1.0",
            "afrobench_lite_pin": "f4d4b3de",
            "waxal_pin": "pending",
        },
    )
    out = HERE / "report.real.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"mean fertility premium: {report['structural_economics']['mean_fertility_premium']:.4f}")
    print(f"script premiums: {report['structural_economics'].get('script_premiums')}")

    if not SCORER.exists():
        print(f"scorer not built at {SCORER}; run: cargo build --release in {SCORER.parent}", file=sys.stderr)
        return 2
    r = subprocess.run(
        [str(SCORER), "score", "--report", str(out), "--weights", str(WEIGHTS)],
        capture_output=True, text=True,
    )
    print(r.stdout)
    print(f"exit code: {r.returncode} ({'PASS' if r.returncode == 0 else 'below threshold'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
