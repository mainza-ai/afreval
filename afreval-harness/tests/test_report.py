"""Tests for the ModelReport builder (§3.2 report contract)."""
import pytest

from harness.report import build_report, mean_fertility_premium, script_premiums
from harness.tokenizer_eval import (
    ETHIOPIC,
    LATIN,
    NKO,
    LanguageResult,
    ScriptSummary,
    TokenizerEvalResult,
)


def _result() -> TokenizerEvalResult:
    langs = [
        LanguageResult(lang="eng", script=LATIN, tokens=100, words=100, chars=500,
                       bytes=600, fertility=1.0, cpt=5.0, bpt=6.0, premium=1.0),
        LanguageResult(lang="yor", script=LATIN, tokens=300, words=100, chars=300,
                       bytes=400, fertility=3.0, cpt=1.0, bpt=1.333, premium=3.0),
        LanguageResult(lang="amh", script=ETHIOPIC, tokens=500, words=100, chars=300,
                       bytes=700, fertility=5.0, cpt=0.6, bpt=1.4, premium=5.0),
    ]
    by_script = {
        LATIN: ScriptSummary(script=LATIN, languages=["eng", "yor"],
                             mean_fertility_premium=2.0, mean_cpt=3.0, mean_bpt=3.6),
        ETHIOPIC: ScriptSummary(script=ETHIOPIC, languages=["amh"],
                                mean_fertility_premium=5.0, mean_cpt=0.6, mean_bpt=1.4),
        NKO: ScriptSummary(script=NKO, languages=[], mean_fertility_premium=None,
                           mean_cpt=None, mean_bpt=None),
    }
    return TokenizerEvalResult(tokenizer="t", baseline="eng",
                               languages=langs, by_script=by_script, english_cpt=5.0)


def test_mean_premium_excludes_baseline():
    r = _result()
    assert mean_fertility_premium(r) == pytest.approx((3.0 + 5.0) / 2)


def test_script_premiums_are_independent():
    r = _result()
    sp = script_premiums(r)
    assert sp[LATIN] == pytest.approx(2.0)
    assert sp[ETHIOPIC] == pytest.approx(5.0)


def test_build_report_contract():
    rep = build_report(
        "m", waxal_macro_wer=0.4, afrobench_lite_accuracy=0.6,
        bias_corrected_judge_score=80.0, mean_fertility_premium=2.5,
        pins={"afri_fertility_pin": "p", "afrobench_lite_pin": "p", "waxal_pin": "p"},
    )
    assert rep["structural_economics"]["mean_fertility_premium"] == 2.5
    assert rep["linguistic_fidelity"]["waxal_macro_wer"] == 0.4
    assert "script_premiums" not in rep["structural_economics"]


def test_report_from_eval_carries_script_detail():
    rep = build_report(
        "m", waxal_macro_wer=0.4, afrobench_lite_accuracy=0.6,
        bias_corrected_judge_score=80.0, mean_fertility_premium=2.5,
        pins={"afri_fertility_pin": "p", "afrobench_lite_pin": "p", "waxal_pin": "p"},
        script_premiums={"latin": 2.0, "ethiopic": 5.0},
    )
    assert rep["structural_economics"]["script_premiums"]["ethiopic"] == 5.0
