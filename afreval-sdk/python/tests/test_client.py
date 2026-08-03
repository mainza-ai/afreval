"""SDK tests — deterministic, offline (calls the local Rust scorer binary)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from afreval_sdk import AfrevalClient, CertRequest  # noqa: E402

WEIGHTS = """vertical: test
version: 1
weights:
  linguistic_fidelity: 0.5
  cultural_safety: 0.2
  structural_economics: 0.3
linguistic_fidelity_internal:
  acoustic: 0.6
  textual: 0.4
threshold: 70.0
"""


def req() -> CertRequest:
    return CertRequest(
        model_id="t",
        waxal_macro_wer=0.38,
        afrobench_lite_accuracy=0.62,
        bias_corrected_judge_score=78.0,
        mean_fertility_premium=1.8,
        harness_pins={"afri_fertility_pin": "p", "afrobench_lite_pin": "p", "waxal_pin": "p"},
        weights_yaml=WEIGHTS,
    )


def test_cert_is_deterministic():
    c = AfrevalClient()
    a = c.certify(req())
    b = c.certify(req())
    assert a.cert_sha256 == b.cert_sha256
    assert a.context_score == b.context_score


def test_cert_values():
    c = AfrevalClient().certify(req())
    # acoustic = 62, textual = 62, LF = 62; CS = 78; SE = 100/1.8 = 55.55
    expected = 0.5 * 62.0 + 0.2 * 78.0 + 0.3 * (100.0 / 1.8)
    assert abs(c.context_score - expected) < 1e-6
    assert c.pass_ is False  # below threshold 70
