"""Code-mixing metrics — CMI, enhanced CMI, I-index, M-index (§3.2).

Implements the math formalized in the Research doc (the Bible only says
Linguistic Fidelity is "weighted toward code-switching robustness"; the
formulas live here). Gap-analysis: code-mixing metrics, 2026-08-05.

Formulas (per the wiki's [code-mixing] concept page):
  CMI            = 1 - (W_major + N_li) / T_total
  CMI_enhanced   = α·(switch-point ratio) + β·(legacy CMI)     α+β = 1
  I-index        = probability a token is a switch point
  M-index        = inequality of the language-tag distribution (1 - normalized Gini)

All inputs are tokenized text with a per-token language tag. A language tagger
is out of scope here; callers provide `language(text) -> tag` or a per-token
tag sequence. The metrics are deterministic given the tags.

[code-mixing]: ../../wiki/concepts/code-mixing.md
"""
from __future__ import annotations

import re
from collections import Counter

_WORD_SPLIT = re.compile(r"\s+")


def tokenize(text: str) -> list[str]:
    """Coarse whitespace tokenization (matches the harness's word counting)."""
    return [w for w in _WORD_SPLIT.split(text) if w]


def _tag_tokens(tokens: list[str], tag: callable) -> list[str]:
    return [tag(t) or "unk" for t in tokens]


def switch_points(tags: list[str]) -> int:
    """Number of alternation points: adjacent token pairs with different tags."""
    return sum(1 for a, b in zip(tags, tags[1:]) if a != b)


def cmi(tokens: list[str], tags: list[str], language_independent: set[str] | None = None) -> float:
    """Legacy Code-Mixing Index.

    CMI = 1 - (W_major + N_li) / T_total
    High CMI (near 1) = heavily code-mixed; low (near 0) = monolingual.
    """
    if not tokens:
        return 0.0
    li = language_independent or set()
    major_count = Counter(tags).most_common(1)[0][1] if tags else 0
    n_li = sum(1 for t in tokens if t in li)
    return 1.0 - (major_count + n_li) / len(tokens)


def cmi_enhanced(tokens: list[str], tags: list[str], alpha: float = 0.5,
                 language_independent: set[str] | None = None) -> float:
    """Enhanced CMI: α·switch-point-ratio + β·legacy-CMI (α+β=1)."""
    if not tokens:
        return 0.0
    beta = 1.0 - alpha
    switch_ratio = switch_points(tags) / len(tokens)
    return alpha * switch_ratio + beta * cmi(tokens, tags, language_independent)


def i_index(tokens: list[str], tags: list[str]) -> float:
    """Integration-index: probability a token is a switch point.

    I-index = (# tokens adjacent to a switch) / (total tokens).
    """
    if not tokens:
        return 0.0
    switches = set()
    for i in range(len(tags) - 1):
        if tags[i] != tags[i + 1]:
            switches.add(i)
            switches.add(i + 1)
    return len(switches) / len(tokens)


def m_index(tags: list[str]) -> float:
    """Multilingual Index: inequality of the language-tag distribution.

    M-index = 1 - (normalized Gini). 1.0 = perfectly equal mix across the
    languages present; 0.0 = fully skewed to one language.
    """
    counts = sorted(Counter(tags).values())
    n = len(counts)
    if n == 0:
        return 0.0
    total = sum(counts)
    if total == 0:
        return 0.0
    # Gini coefficient (correct form): Σ(2i - n - 1)·x_i / (n²·μ) over the
    # sorted distribution.
    gini = sum((2 * (i + 1) - n - 1) * c for i, c in enumerate(counts)) / (n * n * (total / n))
    gini = max(0.0, min(1.0, gini))
    return 1.0 - gini


def measure(text: str, tag: callable, language_independent: set[str] | None = None,
            alpha: float = 0.5) -> dict[str, float]:
    """All four metrics for a tagged utterance, as one dict."""
    tokens = tokenize(text)
    tags = _tag_tokens(tokens, tag)
    return {
        "tokens": len(tokens),
        "switch_points": switch_points(tags),
        "cmi": cmi(tokens, tags, language_independent),
        "cmi_enhanced": cmi_enhanced(tokens, tags, alpha, language_independent),
        "i_index": i_index(tokens, tags),
        "m_index": m_index(tags),
    }
