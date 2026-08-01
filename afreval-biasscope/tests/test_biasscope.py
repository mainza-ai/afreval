"""§3.3 tests — deterministic (mock judge) + perturbation program."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from judge.backends import MockJudge  # noqa: E402
from probes.perturbation_program import perturb, seed_from_reference_suite  # noqa: E402


def test_mock_generosity_bias():
    j = MockJudge()
    en = j.judge("x", "eng")
    am = j.judge("x", "amh")
    assert am.score > en.score
    assert not en.accepted and am.accepted


def test_acceptance_delta_is_positive():
    j = MockJudge()
    langs = ["eng", "fra", "swh", "yor", "hau", "ibo", "amh"]
    rates = {lang: float(j.judge("x", lang).accepted) for lang in langs}
    assert max(rates.values()) - min(rates.values()) > 0.5


def test_perturb_none_is_identity():
    suite = {"eng": ["a b"], "amh": ["አ በ"]}
    item = seed_from_reference_suite(suite)[0]
    assert perturb(item, "none").translations == item.translations


def test_perturb_code_switch_marks_provenance():
    suite = {"eng": ["a b"], "amh": ["አ በ"]}
    item = seed_from_reference_suite(suite)[0]
    p = perturb(item, "colloquial")
    assert p.perturbed == "colloquial"
    assert p.item_id.endswith(":colloquial")
