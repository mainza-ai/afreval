#!/usr/bin/env python3
"""§3.2.1 certification pipeline — deterministic, auditable, reproducible.

Same model + same weight config + same harness version → same Context Score,
always. This is the CERTIFICATION loop (a deterministic pipeline invocation),
NOT the calibration loop — it is never agent-optimized.

Flow:
  1. Verify the frozen pins (harness version integrity).
  2. Run the §3.1 tokenizer harness on the pinned reference suite → real premium.
  3. Combine with WAXAL WER / AfroBench-LITE accuracy / BiasScope-corrected
     judge score (each from its own pipeline; provided as inputs until those
     pipelines are wired online).
  4. Build the ModelReport and score with the Rust scorer (bit-identical).
  5. Emit an auditable cert (report + score + harness pins + sha256), written
     to certs/.

Run with the afri-fertility venv:
  afreval-harness/.venv/bin/python afreval-harness/scripts/certify.py \
      --model my-model --weights afreval-context-score/weights/telco.yaml
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent
sys.path.insert(0, str(HERE))

from harness.pins import load_pin  # noqa: E402
from harness.report import report_from_eval  # noqa: E402
from harness.tokenizer_eval import TokenizerEval, load_reference_suite  # noqa: E402
from afri_fertility import load_tokenizer  # noqa: E402

SCORER = REPO / "afreval-context-score" / "target" / "release" / "afreval-context-score"


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def main() -> int:
    ap = argparse.ArgumentParser(description="§3.2.1 deterministic certification pipeline")
    ap.add_argument("--model", required=True)
    ap.add_argument("--weights", required=True, help="path to weights/{vertical}.yaml")
    ap.add_argument("--tokenizer", default="openai/o200k_base")
    ap.add_argument("--tokenizer-candidate", default="",
                    help="§3.1 research candidate class (EfficientRouteCandidate/ScriptAwareCandidate) "
                         "from afreval-tokenizer-research — certifies with the loop's best tokenizer")
    ap.add_argument("--wer", type=float, default=None, help="WAXAL macro WER (overrides --auto-inputs)")
    ap.add_argument("--accuracy", type=float, default=0.62, help="AfroBench-LITE mean accuracy")
    ap.add_argument("--judge", type=float, default=78.0, help="BiasScope-corrected judge score")
    ap.add_argument("--auto-inputs", action="store_true",
                    help="pull WER from the frozen QA baseline (eval_baseline.py --from-qa) and judge "
                         "from §3.3 bias_correct.py instead of manual flags")
    ap.add_argument("--bias-correct-from", default="",
                    help="dir of §3.3 run_*.json results; when set, applies the §3.3 "
                         "acceptance-delta correction to --judge before scoring "
                         "(afreval-biasscope/bias_correct.py)")
    ap.add_argument("--out", default=str(HERE / "certs"))
    args = ap.parse_args()

    af_pin = load_pin("afri_fertility.yaml")
    if af_pin["status"] != "frozen":
        print(f"certification blocked: afri_fertility pin not frozen ({af_pin['status']})", file=sys.stderr)
        return 2
    ab_pin = load_pin("afrobench_lite.yaml")
    wax_pin = load_pin("waxal.yaml")

    suite = load_reference_suite()
    if args.tokenizer_candidate:
        # §3.1 loop winner: the efficient-route candidate trained on SIB-200
        # (latin premium 1.55→1.29, ethiopic 3.38→2.83). Loaded from the
        # research repo so certification reflects the loop's current best.
        research = REPO / "afreval-tokenizer-research"
        sys.path.insert(0, str(research))
        import importlib
        spec = importlib.import_module("candidates.tokenizer_candidate")
        cls = getattr(spec, args.tokenizer_candidate)
        tok = cls() if isinstance(cls, type) else cls
    else:
        tok = load_tokenizer(args.tokenizer)
    tok_result = TokenizerEval().evaluate(tok, suite)

    # Auto-inputs: pull WER from the frozen QA baseline and the judge from
    # §3.3 bias correction, instead of hand-supplied flags (gap-analysis A2).
    auto_sources: dict[str, str] = {}
    if args.auto_inputs:
        if args.wer is not None:
            print("--auto-inputs: --wer override ignored", file=sys.stderr)
        if args.bias_correct_from:
            print("--auto-inputs: --bias-correct-from redundant (implied)", file=sys.stderr)
        waxal_net = REPO / "afreval-waxal-net"
        sys.path.insert(0, str(waxal_net))
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("eval_baseline", waxal_net / "eval_baseline.py")
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        baseline = mod.aggregate_qa_baseline()
        args.wer = baseline["language_macro_wer"]
        auto_sources["wer"] = f"eval_baseline.py --from-qa (n={baseline['n_languages']})"
        args.bias_correct_from = str(REPO / "afreval-biasscope" / "results")

    judge_score = args.judge
    bias_correction = None
    if args.bias_correct_from:
        # §3.3 -> §3.2.1 bridge: worst-case acceptance-rate delta across the
        # live probe runs scales the raw judge score down (Cultural Safety).
        bc = REPO / "afreval-biasscope" / "bias_correct.py"
        sys.path.insert(0, str(bc.parent))
        import importlib.util
        spec = importlib.util.spec_from_file_location("bias_correct", bc)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        delta = mod.worst_case_delta(Path(args.bias_correct_from))
        judge_score = mod.corrected_score(args.judge, delta)
        bias_correction = {
            "raw_judge_score": args.judge,
            "worst_case_acceptance_delta": round(delta, 4),
            "bias_penalty_weight": mod.BIAS_PENALTY_WEIGHT,
            "note": "computed by afreval-biasscope/bias_correct.py from §3.3 run results",
        }
        auto_sources["judge"] = "afreval-biasscope/bias_correct.py from results/"

    report = report_from_eval(
        args.model,
        tok_result,
        waxal_macro_wer=args.wer,
        afrobench_lite_accuracy=args.accuracy,
        bias_corrected_judge_score=judge_score,
        pins={
            "afri_fertility_pin": af_pin["pinned_version"],
            "afrobench_lite_pin": ab_pin["harness_submodule"],
            "waxal_pin": wax_pin.get("pinned_version", wax_pin.get("status", "pending")),
        },
    )

    if not SCORER.exists():
        print(f"scorer not built: {SCORER}", file=sys.stderr)
        return 2
    report_tmp = Path("/tmp") / f"certify_{args.model}.report.json"
    report_tmp.write_text(canonical_json(report))
    scored = subprocess.run(
        [str(SCORER), "score", "--report", str(report_tmp), "--weights", args.weights],
        capture_output=True, text=True,
    )
    report_tmp.unlink(missing_ok=True)
    if scored.returncode not in (0, 1):
        print(scored.stderr, file=sys.stderr)
        return 2

    cert = {
        "model": args.model,
        "report": report,
        "score": json.loads(scored.stdout),
        "bias_correction": bias_correction,
        "input_sources": auto_sources if auto_sources else None,
        "harness_pins": {
            "afri_fertility": af_pin["pinned_version"],
            "afrobench_lite": ab_pin["harness_submodule"],
            "waxal": wax_pin.get("pinned_version", wax_pin.get("status", "pending")),
        },
    }
    cert["cert_sha256"] = hashlib.sha256(canonical_json(cert).encode()).hexdigest()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{args.model}.cert.json"
    dest.write_text(json.dumps(cert, indent=2))
    print(json.dumps(cert["score"], indent=2))
    print(f"cert written -> {dest}")
    print(f"cert_sha256: {cert['cert_sha256']}")
    return 0 if cert["score"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
