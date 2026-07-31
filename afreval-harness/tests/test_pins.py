"""Tests for pin loading and the AfroBench-LITE vendored validation."""
import pytest

from harness.afrobench_eval import LITEPinError, validate_vendored_lite
from harness.pins import load_all_pins


def test_all_pins_load():
    pins = load_all_pins()
    assert set(pins) == {"afri_fertility.yaml", "afrobench_lite.yaml", "waxal.yaml"}


def test_afri_fertility_pin_frozen():
    pin = load_all_pins()["afri_fertility.yaml"]
    assert pin["status"] == "frozen"
    assert pin["baseline_language"] == "eng"
    assert len(pin["vendored_commit"]) == 40


def test_waxal_pin_pending():
    pin = load_all_pins()["waxal.yaml"]
    assert pin["status"] == "pending-freeze"  # Phase 0 not complete until acquired+QA'd


def test_afrobench_lite_matches_vendored():
    info = validate_vendored_lite()
    assert info["group"] == "afrobench_lite"
    assert len(info["tasks"]) == 7
    assert len(info["pinned_languages"]) == 14
    assert "afrimgsm_cot_tasks" in info["tasks"]


def test_validate_detects_drift(tmp_path, monkeypatch):
    import harness.afrobench_eval as m

    pin = m.load_lite_pin()
    bad = dict(pin)
    bad["task_set"] = pin["task_set"] + ["drifted_task"]
    monkeypatch.setattr(m, "load_lite_pin", lambda: bad)
    with pytest.raises(LITEPinError, match="diverges"):
        validate_vendored_lite(bad)
