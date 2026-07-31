"""Tests for the WAXAL acoustic scoring module."""
import pytest

from harness.waxal_eval import cer, corpus_wer_cer, score_transcription, wer


def test_wer_exact():
    assert wer("hello world", "hello world") == 0.0


def test_wer_substitution():
    # one word substituted out of four
    assert wer("the quick brown fox", "the quick red fox") == pytest.approx(0.25)


def test_wer_insertion():
    assert wer("a b", "a b c") == pytest.approx(0.5)


def test_wer_empty_reference():
    assert wer("", "") == 0.0
    assert wer("", "x") == 1.0


def test_cer_char_level():
    # transposition/substitution at character level
    assert cer("abc", "abd") == pytest.approx(1 / 3)


def test_score_transcription_record():
    s = score_transcription("the patient takes medicine", "the patient take medicine")
    assert s.reference == "the patient takes medicine"
    assert s.wer == pytest.approx(1 / 4)
    assert s.cer > 0.0


def test_corpus_macro_average():
    scores = [score_transcription("a b c d", "a b c d"), score_transcription("x y", "x")]  # 0.0 and 0.5
    w, c = corpus_wer_cer(scores)
    assert w == pytest.approx(0.25)
    assert 0.0 <= c <= 1.0
