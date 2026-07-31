"""Unit tests for metrics module."""
import pytest
from afri_fertility.core.metrics import (
    fertility, premium, cpt, bpt, context_efficiency, relative_ce, compute_metrics,
)


def test_fertility_basic():
    assert fertility(10, 5) == pytest.approx(2.0)


def test_fertility_parity():
    # Same tokens as words → fertility = 1.0
    assert fertility(5, 5) == pytest.approx(1.0)


def test_fertility_zero_words():
    assert fertility(0, 0) == 0.0
    assert fertility(5, 0) == 0.0


def test_premium_baseline_is_one():
    f_eng = 1.5
    p = premium(f_eng, f_eng)
    assert p == pytest.approx(1.0)


def test_premium_higher_than_baseline():
    assert premium(3.0, 1.5) == pytest.approx(2.0)


def test_premium_zero_baseline():
    assert premium(2.0, 0.0) == 0.0


def test_cpt_basic():
    assert cpt(50, 10) == pytest.approx(5.0)


def test_cpt_zero_tokens():
    assert cpt(50, 0) == 0.0


def test_bpt_basic():
    assert bpt(100, 10) == pytest.approx(10.0)


def test_context_efficiency():
    ce = context_efficiency(128000, 5.0)
    assert ce == pytest.approx(640000.0)


def test_relative_ce_baseline_is_one():
    ce = context_efficiency(128000, 5.0)
    assert relative_ce(ce, ce) == pytest.approx(1.0)


def test_relative_ce_reduced():
    ce_lang = context_efficiency(128000, 2.5)
    ce_base = context_efficiency(128000, 5.0)
    assert relative_ce(ce_lang, ce_base) == pytest.approx(0.5)


def test_compute_metrics_returns_object():
    m = compute_metrics(tokens=10, words=5, chars=40, bytes_=50, tokenizer_id="openai/o200k_base")
    assert m.fertility == pytest.approx(2.0)
    assert m.cpt == pytest.approx(4.0)
    assert m.bpt == pytest.approx(5.0)
    assert m.tokenizer == "openai/o200k_base"


def test_compute_metrics_empty():
    m = compute_metrics(tokens=0, words=0, chars=0, bytes_=0, tokenizer_id="openai/o200k_base")
    assert m.fertility == 0.0
    assert m.cpt == 0.0
    assert m.bpt == 0.0
