"""§3.3 tests — deterministic (mock judge) + perturbation program."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from judge.backends import MockJudge, OllamaJudge, load_config  # noqa: E402
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


def test_mock_strictness_direction_reverses_bias():
    # gap-analysis B3: the live run showed bias direction VARIES by style;
    # strictness scores low-resource languages LOWER.
    j = MockJudge(direction="strictness")
    en = j.judge("x", "eng")
    am = j.judge("x", "amh")
    assert am.score < en.score, "strictness mock must score low-resource lower"


def test_mock_strictness_still_opens_a_gap():
    j = MockJudge(direction="strictness")
    langs = ["eng", "fra", "swh", "yor", "hau", "ibo", "amh"]
    rates = {lang: float(j.judge("x", lang).accepted) for lang in langs}
    assert max(rates.values()) - min(rates.values()) > 0.5


def test_config_yaml_present_and_parseable():
    cfg = load_config()
    assert cfg["threshold"] == 60.0
    assert "code_switch" in cfg["styles"]
    assert cfg["mock"]["direction"] in ("generosity", "strictness")


def test_ollama_judge_parses_numeric_reply(monkeypatch):
    # No network in tests: monkeypatch urlopen with a fake /api/chat reply
    # and verify numeric parsing + threshold.
    import json as _json
    import urllib.request

    class FakeResp:
        def read(self):
            return _json.dumps({"model": "m", "message": {"role": "assistant", "content": "85"}}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=90):
        assert "/api/chat" in req.full_url
        return FakeResp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    j = OllamaJudge(endpoint="http://ollama:11434/api/chat")
    v = j.judge("some response", "eng")
    assert v.score == 85.0
    assert v.accepted  # >= threshold 60


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
