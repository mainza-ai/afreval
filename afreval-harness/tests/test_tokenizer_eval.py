"""Tests for the §3.1 tokenizer harness."""
import pytest

from harness.tokenizer_eval import (
    ETHIOPIC,
    LATIN,
    NKO,
    TokenizerEval,
    english_cpt_regression,
    script_stratify,
)


class _CountingAdapter:
    def __init__(self, tokenizer_id: str, ratio: float = 1.0):
        self.id = tokenizer_id
        self.ratio = ratio

    def count(self, text: str) -> int:
        return max(1, round(len(text.split()) * self.ratio))


def test_script_stratify():
    assert script_stratify("amh") == ETHIOPIC
    assert script_stratify("tir") == ETHIOPIC
    assert script_stratify("nqo") == NKO
    assert script_stratify("yor") == LATIN
    assert script_stratify("swh") == LATIN
    assert script_stratify("zul") == LATIN


def test_english_cpt_regression():
    # Higher CPT = more efficient = better. A >max_pct regression in English CPT fails the candidate.
    assert english_cpt_regression(new_english_cpt=10.5, baseline_english_cpt=10.0)  # improvement: pass
    assert english_cpt_regression(new_english_cpt=9.5, baseline_english_cpt=10.0)  # -5% exactly: pass
    assert not english_cpt_regression(new_english_cpt=9.4, baseline_english_cpt=10.0, max_pct=5.0)  # -6%: fail
    assert not english_cpt_regression(new_english_cpt=9.0, baseline_english_cpt=10.0)  # -10%: fail


def test_evaluate_premium_and_scripts():
    eval_ = TokenizerEval()
    adapter = _CountingAdapter("candidate/base", ratio=1.0)
    corpus = {
        "eng": ["hello world this is a test sentence", "another one here"],
        "yor": ["mo n wa ile ise yi", "eyi ni apere"],
        "amh": ["ይህ የሙከራ ዓረፍተ ነገር ነው", "ሌላ አንድ ነው"],
        "nqo": ["ߞߊ߲ ߘߏ߫ ߦߋ߫ ߢߊ߬", "ߛߓߍߟߌ ߜߘߍ߫"],
    }
    result = eval_.evaluate(adapter, corpus)
    assert result.baseline == "eng"
    # English premium is exactly 1.0
    eng = next(r for r in result.languages if r.lang == "eng")
    assert eng.premium == 1.0
    # Script stratification has all three scored buckets present
    premiums = result.script_premiums()
    assert premiums[LATIN] is not None
    assert premiums[ETHIOPIC] is not None
    assert premiums[NKO] is not None
    # Same meaning -> same word count -> premium == fertility ratio == 1.0 for all
    assert premiums[LATIN] == pytest.approx(1.0)
    assert premiums[ETHIOPIC] == pytest.approx(1.0)
    assert premiums[NKO] == pytest.approx(1.0)
    assert result.english_cpt is not None


def test_evaluate_missing_baseline_raises():
    eval_ = TokenizerEval()
    with pytest.raises(ValueError, match="baseline"):
        eval_.evaluate(_CountingAdapter("x"), {"yor": ["a"]})
