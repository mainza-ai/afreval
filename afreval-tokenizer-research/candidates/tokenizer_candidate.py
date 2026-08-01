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

import json
from pathlib import Path

from afri_fertility import load_tokenizer

from .bpe_trainer import BPECandidate


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


class TrainedBPE:
    """The trained BPE candidate (loads candidates/trained_bpe.json).

    Train it first: `python train_bpe.py --merges <n>`. This is the real §3.1
    candidate space: the agent varies training (corpus mix, merge count,
    pre-tokenization) and re-evaluates.
    """

    def __init__(self):
        p = Path(__file__).resolve().parent / "trained_bpe.json"
        if not p.exists():
            raise FileNotFoundError("run train_bpe.py first (produces candidates/trained_bpe.json)")
        data = json.loads(p.read_text(encoding="utf-8"))
        self._inner = BPECandidate([tuple(m) for m in data["merges"]], data["id"])

    @property
    def id(self) -> str:
        return self._inner.id

    def count(self, text: str) -> int:
        return self._inner.count(text)


_ETHIOPIC_NKO = "\u1200-\u137F\u07C0-\u07FF"


def _has_ethiopic_or_nko(text: str) -> bool:
    for ch in text:
        o = ord(ch)
        if (0x1200 <= o <= 0x137F) or (0x07C0 <= o <= 0x07FF):
            return True
    return False


class ScriptAwareCandidate:
    """§3.1 script-aware pre-tokenization: English-efficient Latin path +
    WAXAL-trained BPE for Ethiopic/N'Ko. Holds English CPT at baseline while
    collapsing the non-Latin premiums.
    """

    id = "candidate/script-aware-v0"

    def __init__(self):
        self._latin = from_afri_fertility("openai/o200k_base")
        self._bpe = TrainedBPE()

    def count(self, text: str) -> int:
        if _has_ethiopic_or_nko(text):
            return self._bpe.count(text)
        return self._latin.count(text)


class EfficientRouteCandidate:
    """Content-driven routing: tokenize with both o200k_base and the trained
    BPE, keep the fewer tokens. English text -> o200k (English-efficient);
    African text (any script) -> BPE (African merges). No language tags, no
    hardcoding — the routing is purely "pick the more efficient tokenizer".
    """

    id = "candidate/efficient-route-v0"

    def __init__(self):
        self._o200k = from_afri_fertility("openai/o200k_base")
        self._bpe = TrainedBPE()

    def count(self, text: str) -> int:
        return min(self._o200k.count(text), self._bpe.count(text))


# The agent swaps the active candidate here (or adds new classes above).
ACTIVE_CANDIDATE = EfficientRouteCandidate
