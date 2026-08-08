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
CERTS_DIR = HARNESS / "certs"
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
    profile: dict | None = None
    methodology: dict | None = None
    rubric_manifest: dict | None = None


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
        profile=cert.get("profile"),
        methodology=cert.get("methodology"),
        rubric_manifest=cert.get("rubric_manifest"),
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


def _load_cert(sha_or_model: str) -> dict:
    """Load a cert by sha256 prefix or by model name from the certs dir."""
    for f in sorted(CERTS_DIR.glob("*.cert.json")):
        try:
            c = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if c.get("cert_sha256", "").startswith(sha_or_model) or c.get("model") == sha_or_model:
            return c
    raise HTTPException(status_code=404, detail=f"cert not found: {sha_or_model}")


@app.get("/v1/certs")
def list_certs() -> dict:
    """List stored certs with model, score, sha, as_of, and staleness."""
    certs = []
    for f in sorted(CERTS_DIR.glob("*.cert.json")):
        try:
            c = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        certs.append({
            "model": c.get("model"),
            "context_score": (c.get("score") or {}).get("context_score"),
            "pass": (c.get("score") or {}).get("pass"),
            "cert_sha256": c.get("cert_sha256"),
            "as_of": (c.get("profile") or {}).get("as_of"),
            "re_cert_after": (c.get("profile") or {}).get("re_cert_after"),
        })
    return {"certifications": certs, "count": len(certs)}


@app.get("/v1/certs/stale")
def stale_certs() -> dict:
    """Certs past their recommended re-certification date."""
    from harness.profile import is_stale

    stale = []
    for f in sorted(CERTS_DIR.glob("*.cert.json")):
        try:
            c = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if is_stale(c):
            stale.append({"model": c.get("model"), "cert_sha256": c.get("cert_sha256"),
                          "as_of": (c.get("profile") or {}).get("as_of"),
                          "re_cert_after": (c.get("profile") or {}).get("re_cert_after")})
    return {"stale": stale, "count": len(stale)}


@app.get("/v1/certs/{sha_or_model}")
def get_cert(sha_or_model: str) -> dict:
    return _load_cert(sha_or_model)


@app.get("/v1/diff")
def diff(base: str, target: str) -> dict:
    """Per-language / per-script / per-vector deltas between two certs."""
    a = _load_cert(base)
    b = _load_cert(target)
    pa, pb = a.get("profile") or {}, b.get("profile") or {}

    def _lang_delta(a_l: dict, b_l: dict) -> dict:
        d = {}
        for k in ("premium", "wer", "cpt"):
            if k in a_l and k in b_l:
                d[f"{k}_delta"] = round(b_l[k] - a_l[k], 4)
        return d

    languages = {}
    all_langs = set(pa.get("languages", {})) | set(pb.get("languages", {}))
    for lang in sorted(all_langs):
        d = _lang_delta(pa.get("languages", {}).get(lang, {}), pb.get("languages", {}).get(lang, {}))
        if d:
            languages[lang] = d

    scripts = {}
    all_scripts = set(pa.get("scripts", {})) | set(pb.get("scripts", {}))
    for s in sorted(all_scripts):
        if s in pa.get("scripts", {}) and s in pb.get("scripts", {}):
            scripts[s] = round(pb["scripts"][s] - pa["scripts"][s], 4)

    va, vb = (a.get("score") or {}).get("vectors", {}), (b.get("score") or {}).get("vectors", {})
    vectors = {k: round(vb[k] - va[k], 4) for k in va if k in vb}

    return {
        "base": {"model": a.get("model"), "cert_sha256": a.get("cert_sha256"), "as_of": (pa or {}).get("as_of")},
        "target": {"model": b.get("model"), "cert_sha256": b.get("cert_sha256"), "as_of": (pb or {}).get("as_of")},
        "context_score_delta": round((b.get("score") or {}).get("context_score", 0) - (a.get("score") or {}).get("context_score", 0), 4),
        "languages": languages,
        "scripts": scripts,
        "vectors": vectors,
    }

