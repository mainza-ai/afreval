"""Pure metric functions: fertility, premium, CPT, BPT, context efficiency."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Metrics:
    tokens: int
    words: int
    chars: int
    bytes: int
    fertility: float
    cpt: float
    bpt: float
    tokenizer: str
    segmentation_method: str


@dataclass(frozen=True, slots=True)
class ContextEfficiency:
    ce_chars: float
    rel_ce: float


def fertility(tokens: int, words: int) -> float:
    """Tokens per word. Returns 0.0 for empty input."""
    if words == 0:
        return 0.0
    return tokens / words


def premium(fertility_lang: float, fertility_baseline: float) -> float:
    """How many times more tokens L uses vs baseline for the same meaning."""
    if fertility_baseline == 0.0:
        return 0.0
    return fertility_lang / fertility_baseline


def cpt(chars: int, tokens: int) -> float:
    """Characters per token."""
    if tokens == 0:
        return 0.0
    return chars / tokens


def bpt(bytes_: int, tokens: int) -> float:
    """UTF-8 bytes per token."""
    if tokens == 0:
        return 0.0
    return bytes_ / tokens


def context_efficiency(window_size: int, cpt_value: float) -> float:
    """Effective real characters that fit in a fixed context window."""
    return window_size * cpt_value


def relative_ce(ce_lang: float, ce_baseline: float) -> float:
    if ce_baseline == 0.0:
        return 0.0
    return ce_lang / ce_baseline


def compute_metrics(
    tokens: int,
    words: int,
    chars: int,
    bytes_: int,
    tokenizer_id: str,
    segmentation_method: str = "uax29",
) -> Metrics:
    f = fertility(tokens, words)
    return Metrics(
        tokens=tokens,
        words=words,
        chars=chars,
        bytes=bytes_,
        fertility=f,
        cpt=cpt(chars, tokens),
        bpt=bpt(bytes_, tokens),
        tokenizer=tokenizer_id,
        segmentation_method=segmentation_method,
    )
