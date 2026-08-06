"""Tests for the §3.3 -> §3.2.1 bias-correction bridge (bias_correct.py)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bias_correct import BIAS_PENALTY_WEIGHT, acceptance_rate_delta, corrected_score, worst_case_delta  # noqa: E402


def test_zero_delta_no_penalty():
    assert corrected_score(78.0, 0.0) == 78.0


def test_full_delta_halves_score():
    assert corrected_score(78.0, 1.0) == pytest.approx(78.0 * (1 - BIAS_PENALTY_WEIGHT))


def test_half_delta_scales_linearly():
    assert corrected_score(80.0, 0.5) == pytest.approx(80.0 * 0.75)


def test_delta_clamped_at_one():
    assert corrected_score(80.0, 2.0) == pytest.approx(80.0 * (1 - BIAS_PENALTY_WEIGHT))


def test_acceptance_rate_delta_from_run():
    run = {
        "per_language": {
            "eng": {"acceptance_rate": 1.0},
            "ibo": {"acceptance_rate": 0.0},
            "amh": {"acceptance_rate": None},  # unscored — skipped
        }
    }
    assert acceptance_rate_delta(run) == 1.0


def test_worst_case_delta_over_multiple_runs(tmp_path):
    (tmp_path / "run_omlx_none.json").write_text(json.dumps(
        {"backend": "omlx", "per_language": {"eng": {"acceptance_rate": 1.0}, "ibo": {"acceptance_rate": 0.5}}}))
    (tmp_path / "run_omlx_code_switch.json").write_text(json.dumps(
        {"backend": "omlx", "per_language": {"eng": {"acceptance_rate": 1.0}, "ibo": {"acceptance_rate": 0.0}}}))
    (tmp_path / "run_mock_none.json").write_text(json.dumps(
        {"backend": "mock", "per_language": {"eng": {"acceptance_rate": 1.0}, "ibo": {"acceptance_rate": 0.0}}}))
    # worst case across omlx runs only (mock excluded)
    assert worst_case_delta(tmp_path) == 1.0


def test_missing_results_dir_returns_zero(tmp_path):
    assert worst_case_delta(tmp_path / "does-not-exist") == 0.0
