"""Code-mixing metric tests — deterministic, no network."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.code_mixing import cmi, cmi_enhanced, i_index, m_index, measure, switch_points  # noqa: E402


def _tag(tok: str) -> str:
    """Dummy tagger: known words are English/Swahili, everything else unk."""
    en = {"the", "is", "a", "and"}
    sw = {"na", "kitu", "mzuri"}
    if tok.lower() in en:
        return "en"
    if tok.lower() in sw:
        return "sw"
    return "unk"


def test_monolingual_cmi_low():
    # all known English words -> no switch points, low CMI
    m = measure("the is a and the is a", _tag)
    assert m["cmi"] < 0.3
    assert m["switch_points"] == 0


def test_code_mixed_cmi_high():
    m = measure("kitu the na mzuri is a thing", _tag)
    assert m["switch_points"] > 0
    assert m["cmi"] > 0.5


def test_cmi_formula_hand_computed():
    # "the X" -> tags [en, unk], T=2, major=1, N_li=0
    assert cmi(["the", "X"], ["en", "unk"]) == 1.0 - 0.5
    # "the the" -> monolingual, T=2, major=2
    assert cmi(["the", "the"], ["en", "en"]) == 1.0 - 1.0


def test_enhanced_alpha_beta():
    tokens = ["kitu", "the", "na", "mzuri", "and"]
    tags = ["sw", "en", "sw", "sw", "en"]
    assert cmi_enhanced(tokens, tags, alpha=1.0) == switch_points(tags) / len(tokens)
    assert cmi_enhanced(tokens, tags, alpha=0.0) == cmi(tokens, tags)


def test_i_index_bounds():
    m = measure("kitu the na mzuri and the cat", _tag)
    assert 0.0 <= m["i_index"] <= 1.0
    assert m["i_index"] > 0  # code-mixed


def test_m_index_equal_vs_skewed():
    equal = m_index(["en", "sw", "en", "sw"])
    skewed = m_index(["en", "en", "en", "sw"])
    assert equal > skewed
    assert equal > 0.9  # perfectly even 2x2
