"""Assemble a Context Score ModelReport from the three frozen harnesses (§3.2).

The Rust scorer (afreval-context-score) consumes a ModelReport JSON:
  linguistic_fidelity.waxal_macro_wer + afrobench_lite_accuracy
  cultural_safety.bias_corrected_judge_score
  structural_economics.mean_fertility_premium

This module builds that report from the Phase 0 harness outputs. Extra fields
(e.g. script-stratified premiums) are carried in the report but ignored by the
scorer (serde ignores unknown keys) — keeping the contract simple while
preserving audit detail.
"""
from __future__ import annotations

from typing import Any

from .tokenizer_eval import TokenizerEvalResult


def mean_fertility_premium(result: TokenizerEvalResult) -> float:
    """Macro-average per-language premium over the pinned set (baseline excluded)."""
    premiums = [
        r.premium
        for r in result.languages
        if r.premium is not None and r.lang != result.baseline
    ]
    if not premiums:
        return 1.0
    return sum(premiums) / len(premiums)


def script_premiums(result: TokenizerEvalResult) -> dict[str, float]:
    """§3.1 script-stratified premiums (latin/ethiopic/nko), scored independently."""
    return {s: v for s, v in result.script_premiums().items() if v is not None}


def build_report(
    model_id: str,
    *,
    waxal_macro_wer: float,
    afrobench_lite_accuracy: float,
    bias_corrected_judge_score: float,
    mean_fertility_premium: float,
    pins: dict[str, str],
    script_premiums: dict[str, float] | None = None,
) -> dict[str, Any]:
    report = {
        "model_id": model_id,
        "harness": pins,
        "linguistic_fidelity": {
            "waxal_macro_wer": waxal_macro_wer,
            "afrobench_lite_accuracy": afrobench_lite_accuracy,
        },
        "cultural_safety": {
            "bias_corrected_judge_score": bias_corrected_judge_score,
        },
        "structural_economics": {
            "mean_fertility_premium": mean_fertility_premium,
        },
    }
    if script_premiums:
        report["structural_economics"]["script_premiums"] = script_premiums
    return report


def report_from_eval(
    model_id: str,
    tokenizer_result: TokenizerEvalResult,
    *,
    waxal_macro_wer: float,
    afrobench_lite_accuracy: float,
    bias_corrected_judge_score: float,
    pins: dict[str, str],
) -> dict[str, Any]:
    """Build a report directly from a §3.1 tokenizer eval result (real premium)."""
    return build_report(
        model_id,
        waxal_macro_wer=waxal_macro_wer,
        afrobench_lite_accuracy=afrobench_lite_accuracy,
        bias_corrected_judge_score=bias_corrected_judge_score,
        mean_fertility_premium=mean_fertility_premium(tokenizer_result),
        pins=pins,
        script_premiums=script_premiums(tokenizer_result),
    )
