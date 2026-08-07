#!/usr/bin/env python3
"""Phase C — AfrEval certification HTTP API (gap-analysis C1).

Wraps the deterministic certification pipeline (certify.py), the §3.5 security
report, and the §3.6 compliance registry behind versioned endpoints. This is
the "tollbooth" — the surface the SDKs call.

Endpoints:
  GET  /v1/health
  POST /v1/certify        -> run the certification pipeline, return the cert
  GET  /v1/security       -> last §3.5 hardening-loop report (per-seam rates)
  GET  /v1/compliance     -> §3.6 citation-currency status

Run:  afreval-harness/.venv/bin/python -m uvicorn api:app --port 8788
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "afreval-harness"))
sys.path.insert(0, str(REPO / "afreval-harness" / "scripts"))

app = FastAPI(title="AfrEval Certification API", version="0.1.0")

HARNESS = REPO / "afreval-harness"
SCORER = REPO / "afreval-context-score" / "target" / "release" / "afreval-context-score"
SECURITY_REPORT = REPO / "afreval-airlock" / "attack" / "report.json"
COMPLIANCE = REPO / "afreval-compliance"


class CertifyRequest(BaseModel):
    model_id: str
    weights_yaml: str
    tokenizer_candidate: str = ""
    waxal_macro_wer: float | None = None
    afrobench_lite_accuracy: float = 0.62
    bias_corrected_judge_score: float = 78.0
    auto_inputs: bool = True


class CertifyResponse(BaseModel):
    model: str
    context_score: float
    vectors: dict
    pass_: bool
    cert_sha256: str
    bias_correction: dict | None = None
    input_sources: dict | None = None


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok", "scorer": SCORER.exists(), "harness_frozen": True}


def _run_certify(req: CertifyRequest) -> dict:
    """Invoke the deterministic certify.py pipeline and return its cert JSON."""
    if not SCORER.exists():
        raise HTTPException(status_code=503, detail=f"scorer not built: {SCORER}")

    out_dir = HARNESS / "certs"
    cmd = [
        sys.executable, str(HARNESS / "scripts" / "certify.py"),
        "--model", req.model_id,
        "--weights", str(REPO / "afreval-context-score" / "weights" / "telco.yaml"),
        "--accuracy", str(req.afrobench_lite_accuracy),
        "--judge", str(req.bias_corrected_judge_score),
        "--out", str(out_dir),
    ]
    if req.tokenizer_candidate:
        cmd += ["--tokenizer-candidate", req.tokenizer_candidate]
    if req.auto_inputs:
        cmd += ["--auto-inputs"]
    else:
        if req.waxal_macro_wer is None:
            raise HTTPException(status_code=400, detail="waxal_macro_wer required when auto_inputs is false")
        cmd += ["--wer", str(req.waxal_macro_wer)]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        raise HTTPException(status_code=502, detail=proc.stderr[-500:])

    cert_path = out_dir / f"{req.model_id}.cert.json"
    if not cert_path.exists():
        raise HTTPException(status_code=502, detail="cert not produced")
    return json.loads(cert_path.read_text(encoding="utf-8"))


@app.post("/v1/certify", response_model=CertifyResponse)
def certify(req: CertifyRequest) -> CertifyResponse:
    cert = _run_certify(req)
    score = cert["score"]
    return CertifyResponse(
        model=cert["model"],
        context_score=score["context_score"],
        vectors=score["vectors"],
        pass_=score["pass"],
        cert_sha256=cert["cert_sha256"],
        bias_correction=cert.get("bias_correction"),
        input_sources=cert.get("input_sources"),
    )


@app.get("/v1/security")
def security() -> dict:
    if not SECURITY_REPORT.exists():
        raise HTTPException(status_code=404, detail="no security report; run afreval-airlock/attack/run_attack.js")
    return json.loads(SECURITY_REPORT.read_text(encoding="utf-8"))


@app.get("/v1/compliance")
def compliance() -> dict:
    """§3.6 citation-currency — online check of the registry."""
    proc = subprocess.run(
        [sys.executable, str(COMPLIANCE / "check_currency.py")],
        capture_output=True, text=True,
    )
    lines = proc.stdout.strip().splitlines()
    return {
        "exit": proc.returncode,
        "lines": lines,
        "current": "100% (7/7 current)" in proc.stdout,
    }
