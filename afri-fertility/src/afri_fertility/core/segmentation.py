"""UAX-29 word segmentation, NFC normalization, char/byte counting."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

import regex

try:
    import uniseg.wordbreak as _ub

    _HAS_UNISEG = True
except ImportError:  # pragma: no cover
    _HAS_UNISEG = False


@dataclass(frozen=True, slots=True)
class SegmentationResult:
    words: int
    chars: int
    bytes: int
    method: str  # "uax29" | "regex"


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _count_words_uax29(text: str) -> int:
    """Count words using UAX-29 word-break algorithm via uniseg."""
    count = 0
    for word in _ub.words(text):
        # UAX-29 yields all segments including whitespace/punctuation clusters.
        # Count only segments that contain at least one word character.
        if regex.search(r"\w", word):
            count += 1
    return count


def _count_words_regex(text: str) -> int:
    return len(regex.findall(r"\w+", text))


def segment(text: str, normalization: str = "NFC") -> SegmentationResult:
    """Normalize, then count words, chars, and UTF-8 bytes."""
    if normalization:
        text = unicodedata.normalize(normalization, text)

    if not text or not text.strip():
        return SegmentationResult(words=0, chars=0, bytes=0, method="uax29" if _HAS_UNISEG else "regex")

    chars = len(text)
    byte_count = len(text.encode("utf-8"))

    if _HAS_UNISEG:
        words = _count_words_uax29(text)
        method = "uax29"
    else:
        words = _count_words_regex(text)
        method = "regex"

    return SegmentationResult(words=words, chars=chars, bytes=byte_count, method=method)
