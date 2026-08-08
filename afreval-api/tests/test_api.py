"""Phase C API tests — health/security/compliance (no certification run, which
needs the Rust scorer binary and full harness — covered by CI separately)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from api import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_security_report_available():
    # report.json is committed; the endpoint must return per-seam rates
    r = client.get("/v1/security")
    assert r.status_code == 200
    body = r.json()
    assert "total_bypasses" in body
    assert "per_seam" in body


def test_compliance_endpoint():
    r = client.get("/v1/compliance")
    assert r.status_code == 200
    assert "current" in r.json()


def test_certify_requires_scorer():
    # If the scorer is absent the API must fail closed (503), not crash.
    import api
    if not api.SCORER.exists():
        r = client.post("/v1/certify", json={
            "model_id": "t", "weights_yaml": "", "auto_inputs": True,
        })
        assert r.status_code == 503


def test_list_certs():
    r = client.get("/v1/certs")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert "cert_sha256" in body["certifications"][0]


def test_get_cert_by_model_and_sha():
    listing = client.get("/v1/certs").json()["certifications"]
    first = listing[0]
    by_model = client.get(f"/v1/certs/{first['model']}")
    assert by_model.status_code == 200
    assert by_model.json()["model"] == first["model"]
    by_sha = client.get(f"/v1/certs/{first['cert_sha256'][:12]}")
    assert by_sha.status_code == 200


def test_diff_between_certs():
    listing = client.get("/v1/certs").json()["certifications"]
    if len(listing) < 2:
        return  # need two certs to diff
    a, b = listing[0]["cert_sha256"][:12], listing[1]["cert_sha256"][:12]
    r = client.get(f"/v1/diff?base={a}&target={b}")
    assert r.status_code == 200
    body = r.json()
    assert "context_score_delta" in body
    assert "languages" in body and "vectors" in body


def test_stale_certs_endpoint():
    r = client.get("/v1/certs/stale")
    assert r.status_code == 200
    assert "count" in r.json()
