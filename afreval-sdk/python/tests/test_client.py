"""SDK tests — deterministic, offline (calls the local Rust scorer binary)."""
import sys
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

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


class _FakeApi(BaseHTTPRequestHandler):
    """Minimal in-test API: /v1/certify, /v1/security, /v1/compliance."""

    def do_GET(self):
        if self.path == "/v1/security":
            body = b'{"total_variants": 31, "total_bypasses": 0, "per_seam": {}}'
        elif self.path == "/v1/compliance":
            body = b'{"exit": 0, "current": true}'
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/v1/certify":
            import json as _json
            length = int(self.headers.get("content-length", 0))
            payload = _json.loads(self.rfile.read(length))
            body = _json.dumps({
                "model": payload["model_id"],
                "context_score": 55.5,
                "vectors": {"linguistic_fidelity": 57.4, "cultural_safety": 35.0, "structural_economics": 62.8},
                "pass_": False,
                "cert_sha256": "abc123",
                "input_sources": {"wer": "api-mock"},
            }).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):  # silence
        pass


@pytest.fixture(scope="module")
def api_url():
    server = HTTPServer(("127.0.0.1", 0), _FakeApi)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_api_certify(api_url):
    c = AfrevalClient(base_url=api_url)
    r = c.certify_api("m1", tokenizer_candidate="EfficientRouteCandidate", bias_corrected_judge_score=70)
    assert r["context_score"] == 55.5
    assert r["cert_sha256"] == "abc123"


def test_api_security(api_url):
    c = AfrevalClient(base_url=api_url)
    r = c.security_report()
    assert r["total_bypasses"] == 0


def test_api_compliance(api_url):
    c = AfrevalClient(base_url=api_url)
    r = c.compliance()
    assert r["current"] is True
