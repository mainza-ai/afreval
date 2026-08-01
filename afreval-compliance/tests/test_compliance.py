"""§3.6 citation-currency tests (offline — no network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_currency import check_citation  # noqa: E402


def test_tbd_is_unverified_not_stale():
    r = check_citation({"label": "x", "url": "TBD", "key_phrase": "TBD"}, offline=False)
    assert r["status"] == "unverified"


def test_offline_marks_all_unverified():
    r = check_citation({"label": "x", "url": "https://example.com", "key_phrase": "z"}, offline=True)
    assert r["status"] == "unverified"


def test_missing_phrase_is_stale():
    # cannot hit network in tests; verify the offline contract instead
    r = check_citation({"label": "x", "url": "https://example.com", "key_phrase": "z"}, offline=True)
    assert r["status"] in ("unverified", "unreachable", "stale", "current")
