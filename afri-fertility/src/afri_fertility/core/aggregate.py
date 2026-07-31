"""Corpus-level aggregation: sum-then-divide + bootstrap 95% CIs."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .metrics import cpt, bpt, fertility, premium


@dataclass(frozen=True, slots=True)
class TextResult:
    """Per-sentence raw counts (output of tokenize + segment)."""
    tokens: int
    words: int
    chars: int
    bytes: int


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class AggregatedMetrics:
    n_sentences: int
    n_tokens: int
    n_words: int
    n_chars: int
    n_bytes: int
    fertility: float
    cpt: float
    bpt: float
    fertility_ci: ConfidenceInterval
    # premium and premium_ci are computed after joining with baseline aggregate
    premium: float | None = None
    premium_ci: ConfidenceInterval | None = None


def _aggregate_raw(results: list[TextResult]) -> tuple[int, int, int, int]:
    total_tokens = sum(r.tokens for r in results)
    total_words = sum(r.words for r in results)
    total_chars = sum(r.chars for r in results)
    total_bytes = sum(r.bytes for r in results)
    return total_tokens, total_words, total_chars, total_bytes


def aggregate_corpus(
    results: list[TextResult],
    baseline_results: list[TextResult] | None = None,
    bootstrap_n: int = 1000,
    seed: int = 42,
) -> AggregatedMetrics:
    """
    Aggregate per-sentence results using sum-then-divide (not mean-of-ratios).
    Provides bootstrap 95% CI over sentences for fertility (and premium if baseline given).
    """
    if not results:
        ci = ConfidenceInterval(low=0.0, high=0.0)
        return AggregatedMetrics(
            n_sentences=0, n_tokens=0, n_words=0, n_chars=0, n_bytes=0,
            fertility=0.0, cpt=0.0, bpt=0.0, fertility_ci=ci,
        )

    n_tokens, n_words, n_chars, n_bytes = _aggregate_raw(results)
    f = fertility(n_tokens, n_words)
    c = cpt(n_chars, n_tokens)
    b = bpt(n_bytes, n_tokens)

    # Bootstrap CI for fertility
    rng = np.random.default_rng(seed)
    n = len(results)
    tokens_arr = np.array([r.tokens for r in results])
    words_arr = np.array([r.words for r in results])

    boot_fertility = np.empty(bootstrap_n)
    for i in range(bootstrap_n):
        idx = rng.integers(0, n, size=n)
        bt = tokens_arr[idx].sum()
        bw = words_arr[idx].sum()
        boot_fertility[i] = bt / bw if bw > 0 else 0.0

    f_ci = ConfidenceInterval(
        low=float(np.percentile(boot_fertility, 2.5)),
        high=float(np.percentile(boot_fertility, 97.5)),
    )

    p = None
    p_ci = None
    if baseline_results:
        bn_tokens, bn_words, _, _ = _aggregate_raw(baseline_results)
        baseline_f = fertility(bn_tokens, bn_words)
        p = premium(f, baseline_f)

        baseline_tokens_arr = np.array([r.tokens for r in baseline_results])
        baseline_words_arr = np.array([r.words for r in baseline_results])
        nb = len(baseline_results)

        boot_premium = np.empty(bootstrap_n)
        rng2 = np.random.default_rng(seed)
        for i in range(bootstrap_n):
            idx_l = rng2.integers(0, n, size=n)
            idx_b = rng2.integers(0, nb, size=nb)
            bt_l = tokens_arr[idx_l].sum()
            bw_l = words_arr[idx_l].sum()
            bt_b = baseline_tokens_arr[idx_b].sum()
            bw_b = baseline_words_arr[idx_b].sum()
            fl = bt_l / bw_l if bw_l > 0 else 0.0
            fb = bt_b / bw_b if bw_b > 0 else 0.0
            boot_premium[i] = fl / fb if fb > 0 else 0.0

        p_ci = ConfidenceInterval(
            low=float(np.percentile(boot_premium, 2.5)),
            high=float(np.percentile(boot_premium, 97.5)),
        )

    return AggregatedMetrics(
        n_sentences=len(results),
        n_tokens=n_tokens,
        n_words=n_words,
        n_chars=n_chars,
        n_bytes=n_bytes,
        fertility=f,
        cpt=c,
        bpt=b,
        fertility_ci=f_ci,
        premium=p,
        premium_ci=p_ci,
    )
