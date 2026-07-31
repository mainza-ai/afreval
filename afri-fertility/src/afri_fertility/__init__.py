"""afri-fertility — measure the tokenization tax on African languages."""
from __future__ import annotations

from .core.metrics import Metrics, compute_metrics
from .core.segmentation import segment, normalize
from .tokenizers import REGISTRY, TokenizerAdapter, TokenizerUnavailableError, TokenizerNotFoundError
from .cost.model import CostResult, compute_cost
from .cost.prices import PriceTable, load_default_prices
from .cost.fx import FXTable, load_default_fx

# Ensure tiktoken adapters are registered at import time (fast, no network).
# HF adapters are registered lazily — call load_tokenizer() or
# afri_fertility.tokenizers.hf_adapter.register_all_hf() to opt in.
from .tokenizers import tiktoken_adapter as _tiktoken  # noqa: F401


def load_tokenizer(id: str) -> TokenizerAdapter:
    """Return a registered tokenizer adapter by id (e.g. 'openai/o200k_base')."""
    from .tokenizers.hf_adapter import register_all_hf, _get_hf_token
    register_all_hf(hf_token=_get_hf_token())
    return REGISTRY.get(id)


def measure_text(
    text: str,
    tokenizer: str = "openai/o200k_base",
    normalization: str = "NFC",
) -> Metrics:
    """
    Tokenize text and return fertility metrics.

    Args:
        text: Input text (any language).
        tokenizer: Tokenizer id from the registry.
        normalization: Unicode normalization form (default NFC).

    Returns:
        Metrics with tokens, words, chars, bytes, fertility, cpt, bpt.
    """
    import unicodedata as _ud
    adapter = REGISTRY.get(tokenizer)
    normed = _ud.normalize(normalization, text) if normalization else text
    seg = segment(normed, normalization="")
    n_tokens = adapter.count(normed)
    return compute_metrics(
        tokens=n_tokens,
        words=seg.words,
        chars=seg.chars,
        bytes_=seg.bytes,
        tokenizer_id=adapter.id,
        segmentation_method=seg.method,
    )


def cost_of(
    text: str,
    lang: str = "eng",
    models: list[str] | None = None,
    prices: PriceTable | None = None,
    fx: FXTable | None = None,
    out_in_ratio: float = 1.0,
    local_currencies: list[str] | None = None,
) -> list[CostResult]:
    """
    Widget backend (FR-26): given raw text + language + models, return cost per model.

    Uses tiktoken/HF backends only (no API keys needed).
    """
    if models is None:
        models = REGISTRY.available_ids()
    if prices is None:
        prices = load_default_prices()
    if fx is None:
        fx = load_default_fx()

    # Measure fertility per model
    results = []
    for tok_id in models:
        try:
            m = measure_text(text, tokenizer=tok_id)
        except Exception:
            continue

        if tok_id not in prices:
            continue

        # Approximate baseline with English fertility from same tokenizer
        baseline_fertility = m.fertility  # fallback: same as lang → relative_cost = 1.0

        result = compute_cost(
            language=lang,
            tokenizer_id=tok_id,
            fertility=m.fertility,
            baseline_fertility=baseline_fertility,
            prices=prices,
            fx=fx,
            out_in_ratio=out_in_ratio,
            local_currencies=local_currencies,
        )
        results.append(result)

    return results


def run_study(config) -> "StudyResult":
    """Run a complete study from a StudyConfig or YAML path."""
    from .study.runner import run_study as _run
    return _run(config)


__all__ = [
    "measure_text",
    "cost_of",
    "run_study",
    "load_tokenizer",
    "Metrics",
    "CostResult",
    "segment",
    "normalize",
    "REGISTRY",
    "TokenizerAdapter",
    "TokenizerUnavailableError",
    "TokenizerNotFoundError",
    "PriceTable",
    "FXTable",
]
