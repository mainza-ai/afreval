"""§3.1 tokenizer candidate — THE MUTABLE ARTIFACT.

The agent edits THIS file to construct candidate vocabularies. The frozen
harness (harness/tokenizer_eval.py) is never touched. Any candidate must
implement the two-method protocol:
    .id                       -> str
    .count(text: str) -> int  # tokens produced for text

Rules from program.md:
  - Minimize script-stratified mean fertility premium (latin/ethiopic/nko).
  - Do NOT regress English CPT by more than 5% vs baseline.
  - N'Ko and Ethiopic premiums are scored independently — a Latin win does
    not offset a regression on either.
"""
from __future__ import annotations

from afri_fertility import load_tokenizer


def from_afri_fertility(tokenizer_id: str):
    """Wrap a registered afri-fertility adapter as a candidate (baselines only)."""
    return load_tokenizer(tokenizer_id)


class ByteFallbackCandidate:
    """Starting template: byte-level tokens (language-neutral fertility).

    Expected verdict: premium near 1.0 (fair per script) BUT English CPT
    regresses far more than 5% vs baseline — the loop must reject it. This
    is the worst-case anchor: zero tax, useless context efficiency.
    """

    id = "candidate/byte-fallback-v0"

    def count(self, text: str) -> int:
        return len(text.encode("utf-8"))


class CharacterCandidate:
    """Coarse baseline: one token per Unicode code point.

    Script-fair (every script's chars are counted 1:1) but fertility is high
    for agglutinative languages and English CPT regresses vs BPE baseline.
    """

    id = "candidate/char-v0"

    def count(self, text: str) -> int:
        return len(text)


# The agent swaps the active candidate here (or adds new classes above).
ACTIVE_CANDIDATE = ByteFallbackCandidate
