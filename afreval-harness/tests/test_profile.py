"""Context Profile tests — the per-language/script vector behind the scalar (R1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.profile import build_profile, cert_age_days, is_stale  # noqa: E402


def _result():
    from harness.tokenizer_eval import TokenizerEval, load_reference_suite
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "afreval-tokenizer-research"))
    from candidates.tokenizer_candidate import EfficientRouteCandidate
    suite = load_reference_suite()
    return TokenizerEval().evaluate(EfficientRouteCandidate(), suite)


def test_profile_has_languages_scripts_dimensions():
    p = build_profile(_result(), as_of="2026-08-07", re_cert_after_days=90)
    assert "languages" in p and "scripts" in p and "dimensions" in p
    assert len(p["languages"]) >= 7  # reference suite languages
    assert "as_of" in p and "re_cert_after" in p


def test_profile_language_entry_shape():
    p = build_profile(_result(), waxal_per_language_wer={"yor": 0.33}, as_of="2026-08-07")
    entry = p["languages"]["yor"]
    assert "fertility" in entry and "premium" in entry and "cpt" in entry
    assert entry["wer"] == 0.33


def test_profile_scripts_exclude_none():
    p = build_profile(_result(), as_of="2026-08-07")
    assert "nko" not in p["scripts"]  # nko premium is None (not in reference suite)


def test_re_cert_after_is_as_of_plus_cadence():
    p = build_profile(_result(), as_of="2026-08-07", re_cert_after_days=90)
    assert p["re_cert_after"] == "2026-11-05"


def test_is_stale_and_age():
    from datetime import date, timedelta
    old = {"profile": {"as_of": (date.today() - timedelta(days=200)).isoformat(),
                        "re_cert_after": (date.today() - timedelta(days=100)).isoformat()}}
    fresh = {"profile": {"as_of": date.today().isoformat(),
                          "re_cert_after": (date.today() + timedelta(days=90)).isoformat()}}
    assert is_stale(old)
    assert not is_stale(fresh)
    assert cert_age_days(old) == 200


def test_profile_deterministic_across_runs():
    a = build_profile(_result(), as_of="2026-08-07")
    b = build_profile(_result(), as_of="2026-08-07")
    assert a == b
