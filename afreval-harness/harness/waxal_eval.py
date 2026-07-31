"""Acoustic scoring for the WAXAL substrate (§2.1, §3.4).

Pure, deterministic WER/CER over the pinned held-out split. No external
dependencies — edit distance is implemented inline so scores are reproducible
regardless of environment. CER is tracked ALONGSIDE WER (never dropped): for
syllabary-script languages (Ethiopic, N'Ko) the CER/WER ratio reveals
meaningfully higher character-level accuracy than WER alone suggests.
"""
from __future__ import annotations

from dataclasses import dataclass


def _edit_distance(a: list[str], b: list[str]) -> int:
    """Levenshtein distance on token lists (O(len(a)*len(b)), small strings)."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate (insertions+deletions+substitutions)/reference words."""
    ref = reference.split()
    hyp = hypothesis.split()
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


def cer(reference: str, hypothesis: str) -> float:
    """Character error rate over code points."""
    ref = list(reference)
    hyp = list(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


@dataclass(frozen=True)
class TranscriptionScore:
    reference: str
    hypothesis: str
    wer: float
    cer: float


def score_transcription(reference: str, hypothesis: str) -> TranscriptionScore:
    """Score one clip: WER + CER. Returns the frozen, deterministic record."""
    return TranscriptionScore(
        reference=reference,
        hypothesis=hypothesis,
        wer=wer(reference, hypothesis),
        cer=cer(reference, hypothesis),
    )


def corpus_wer_cer(scores: list[TranscriptionScore]) -> tuple[float, float]:
    """Macro-averaged WER/CER across clips (per the WAXAL-NET protocol)."""
    if not scores:
        return 0.0, 0.0
    return sum(s.wer for s in scores) / len(scores), sum(s.cer for s in scores) / len(scores)
