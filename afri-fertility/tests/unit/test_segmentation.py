"""Unit tests for segmentation module."""
import pytest
from afri_fertility.core.segmentation import segment, normalize


def test_normalize_nfc():
    # NFC: composed form
    composed = "é"       # é as single codepoint
    decomposed = "é"    # é as e + combining acute
    assert normalize(decomposed) == composed


def test_empty_string():
    r = segment("")
    assert r.words == 0
    assert r.chars == 0
    assert r.bytes == 0


def test_whitespace_only():
    r = segment("   \t\n")
    assert r.words == 0


def test_simple_english():
    r = segment("Hello world")
    assert r.words == 2
    assert r.chars == 11
    assert r.bytes == 11  # all ASCII


def test_yoruba_diacritics():
    text = "Àwọn ará Nàìjíríà"
    r = segment(text)
    # 3 whitespace-delimited words
    assert r.words == 3
    # chars: count Unicode scalar values, not bytes
    assert r.chars == len(text)
    # bytes: UTF-8 encodes diacritics as multi-byte
    assert r.bytes == len(text.encode("utf-8"))
    assert r.bytes > r.chars  # diacritics inflate byte count


def test_amharic_script():
    # Ethiopic script (no spaces between words in some cases)
    text = "አማርኛ ቋንቋ"
    r = segment(text)
    assert r.words >= 1
    assert r.chars == len(text)
    assert r.bytes == len(text.encode("utf-8"))


def test_method_reported():
    r = segment("Hello world")
    assert r.method in ("uax29", "regex")


def test_nfc_normalization_applied():
    decomposed = "é world"  # 8 chars
    composed = "é world"     # 7 chars
    r = segment(decomposed, normalization="NFC")
    # After NFC, "e + combining acute" → "é" (1 codepoint)
    assert r.chars == len(composed)


def test_no_normalization():
    decomposed = "é world"
    r = segment(decomposed, normalization="")
    # Without NFC, 2 codepoints for the accented char
    assert r.chars == len(decomposed)


def test_arabic_hausa():
    text = "ناجيريا"
    r = segment(text)
    assert r.words >= 1
    assert r.bytes > r.chars  # Arabic chars are multi-byte in UTF-8


def test_hausa_latin():
    text = "Najeriya ta ci gaba"
    r = segment(text)
    assert r.words == 4
