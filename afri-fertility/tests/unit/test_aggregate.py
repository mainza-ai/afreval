"""Unit tests for aggregation: sum-then-divide, bootstrap CIs, properties."""
import pytest
from afri_fertility.core.aggregate import TextResult, aggregate_corpus


def make_results(token_counts, word_counts):
    return [TextResult(tokens=t, words=w, chars=w * 5, bytes=w * 6)
            for t, w in zip(token_counts, word_counts)]


def test_sum_then_divide_not_mean_of_ratios():
    # sum-then-divide: (3+7) / (2+3) = 10/5 = 2.0
    # mean-of-ratios: (3/2 + 7/3) / 2 = (1.5 + 2.333) / 2 = 1.917  (NOT what we want)
    results = make_results([3, 7], [2, 3])
    agg = aggregate_corpus(results, bootstrap_n=10, seed=0)
    assert agg.fertility == pytest.approx(2.0)


def test_premium_baseline_equals_one():
    results = make_results([10, 20], [5, 10])
    # baseline same as lang → premium = 1.0
    agg = aggregate_corpus(results, baseline_results=results, bootstrap_n=10, seed=0)
    assert agg.premium == pytest.approx(1.0)


def test_all_premiums_positive():
    lang = make_results([10, 20, 15], [5, 8, 6])
    base = make_results([5, 10, 8], [5, 8, 6])
    agg = aggregate_corpus(lang, baseline_results=base, bootstrap_n=100, seed=42)
    assert agg.premium is not None
    assert agg.premium > 0


def test_ci_bounds_contain_fertility():
    results = make_results([10, 12, 8, 11, 9], [5, 6, 4, 5, 5])
    agg = aggregate_corpus(results, bootstrap_n=500, seed=42)
    assert agg.fertility_ci.low <= agg.fertility <= agg.fertility_ci.high


def test_empty_results():
    agg = aggregate_corpus([])
    assert agg.fertility == 0.0
    assert agg.n_sentences == 0


def test_single_sentence():
    results = make_results([6], [3])
    agg = aggregate_corpus(results, bootstrap_n=50, seed=0)
    assert agg.fertility == pytest.approx(2.0)
    assert agg.n_sentences == 1


def test_counts_summed_correctly():
    results = [
        TextResult(tokens=5, words=2, chars=10, bytes=12),
        TextResult(tokens=7, words=3, chars=15, bytes=18),
    ]
    agg = aggregate_corpus(results, bootstrap_n=10, seed=0)
    assert agg.n_tokens == 12
    assert agg.n_words == 5
    assert agg.n_chars == 25
    assert agg.n_bytes == 30


def test_premium_ci_present_when_baseline_given():
    results = make_results([10, 20], [5, 10])
    base = make_results([8, 16], [5, 10])
    agg = aggregate_corpus(results, baseline_results=base, bootstrap_n=100, seed=42)
    assert agg.premium_ci is not None
    assert agg.premium_ci.low > 0
