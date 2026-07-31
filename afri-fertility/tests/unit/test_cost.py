"""Unit tests for cost model with hand-checked fixtures."""
import tempfile
from pathlib import Path

import pytest
import yaml

from afri_fertility.cost.prices import PriceTable, ModelPrice
from afri_fertility.cost.fx import FXTable
from afri_fertility.cost.model import compute_cost, annualized_tax


# --- fixtures ---

PRICES_DATA = {
    "snapshot_date": "2026-06-12",
    "currency": "USD",
    "models": {
        "openai/o200k_base": {"price_in": 0.0000025, "price_out": 0.000010},
        "bigscience/bloom": {"price_in": 0.0000001, "price_out": 0.0000001},
    }
}

FX_DATA = {
    "snapshot_date": "2026-06-12",
    "base": "USD",
    "rates": {"NGN": 1360.95, "ZAR": 16.31, "KES": 129.45}
}


@pytest.fixture
def prices_file(tmp_path):
    p = tmp_path / "prices.yaml"
    p.write_text(yaml.dump(PRICES_DATA))
    return p


@pytest.fixture
def fx_file(tmp_path):
    p = tmp_path / "fx.yaml"
    p.write_text(yaml.dump(FX_DATA))
    return p


@pytest.fixture
def prices(prices_file):
    return PriceTable.from_yaml(prices_file)


@pytest.fixture
def fx(fx_file):
    return FXTable.from_yaml(fx_file)


# --- price table tests ---

def test_price_table_loads(prices):
    assert prices.snapshot_date == "2026-06-12"
    assert "openai/o200k_base" in prices


def test_model_price_correct(prices):
    mp = prices.get("openai/o200k_base")
    assert mp.price_in == pytest.approx(0.0000025)
    assert mp.price_out == pytest.approx(0.000010)


def test_unknown_tokenizer_raises(prices):
    with pytest.raises(KeyError):
        prices.get("unknown/model")


# --- fx tests ---

def test_fx_loads(fx):
    assert fx.snapshot_date == "2026-06-12"
    assert "NGN" in fx


def test_ngn_conversion(fx):
    # $1 USD = 1360.95 NGN
    result = fx.convert(1.0, "NGN")
    assert result == pytest.approx(1360.95)


def test_usd_identity(fx):
    result = fx.convert(5.0, "USD")
    assert result == pytest.approx(5.0)


def test_unknown_currency_raises(fx):
    with pytest.raises(KeyError):
        fx.convert(1.0, "XYZ")


def test_zar_conversion(fx):
    result = fx.convert(2.0, "ZAR")
    assert result == pytest.approx(32.62)  # 2.0 * 16.31


# --- cost model tests ---

def test_cost_baseline_relative_is_one(prices, fx):
    # English vs itself: relative_cost = 1.0
    result = compute_cost(
        language="eng",
        tokenizer_id="openai/o200k_base",
        fertility=1.5,
        baseline_fertility=1.5,
        prices=prices,
        fx=fx,
        reference_words=1000,
        out_in_ratio=1.0,
    )
    assert result.relative_cost == pytest.approx(1.0)


def test_cost_yor_higher_than_eng(prices, fx):
    # Yoruba fertility 2× English → relative cost = 2.0
    yor_result = compute_cost("yor", "openai/o200k_base", 3.0, 1.5, prices, fx)
    assert yor_result.relative_cost == pytest.approx(2.0)


def test_token_count_correct(prices, fx):
    # 1000 words × fertility 2.0 = 2000 tokens
    result = compute_cost("yor", "openai/o200k_base", 2.0, 1.0, prices, fx, reference_words=1000)
    assert result.n_tokens == 2000


def test_input_cost_hand_check(prices, fx):
    # 1000 tokens × $0.0000025/token = $0.0025
    result = compute_cost("eng", "openai/o200k_base", 1.0, 1.0, prices, fx, reference_words=1000)
    assert result.input_cost_usd == pytest.approx(0.0025)


def test_total_cost_with_out_in_ratio(prices, fx):
    # 1000 tokens input, 1:1 ratio → 1000 output tokens
    # input: 1000 × $0.0000025 = $0.0025
    # output: 1000 × $0.000010  = $0.01
    # total: $0.0125
    result = compute_cost("eng", "openai/o200k_base", 1.0, 1.0, prices, fx,
                          reference_words=1000, out_in_ratio=1.0)
    assert result.total_cost_usd == pytest.approx(0.0125)


def test_local_currency_costs_present(prices, fx):
    result = compute_cost("yor", "openai/o200k_base", 2.0, 1.0, prices, fx,
                          local_currencies=["NGN", "ZAR"])
    assert "NGN" in result.costs_local
    assert "ZAR" in result.costs_local
    assert result.costs_local["NGN"] > result.costs_local["ZAR"]


def test_ngn_cost_hand_check(prices, fx):
    # total_cost = $0.0125 → NGN = 0.0125 × 1360.95 = 17.011875
    result = compute_cost("eng", "openai/o200k_base", 1.0, 1.0, prices, fx,
                          reference_words=1000, out_in_ratio=1.0,
                          local_currencies=["NGN"])
    assert result.costs_local["NGN"] == pytest.approx(17.011875)


def test_annualized_tax(prices, fx):
    eng = compute_cost("eng", "openai/o200k_base", 1.0, 1.0, prices, fx)
    yor = compute_cost("yor", "openai/o200k_base", 2.0, 1.0, prices, fx)
    tax = annualized_tax(yor, eng, monthly_queries=1_000_000, scenario_name="bank_cs", fx=fx)
    assert tax.annual_premium_usd > 0
    assert "NGN" in tax.annual_premium_local
