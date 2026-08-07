"""Milimo AfrEval Python SDK — programmatic certification.

Two modes:
  - local: deterministic Rust scorer (same bit-identical guarantee as the CLI)
  - api:   the Phase C certification HTTP API (afreval-api) — pass base_url

Each cert is auditable (sha256).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCORER = REPO / "afreval-context-score" / "target" / "release" / "afreval-context-score"


@dataclass(frozen=True)
class Cert:
    model_id: str
    vertical: str
    context_score: float
    linguistic_fidelity: float
    cultural_safety: float
    structural_economics: float
    pass_: bool
    cert_sha256: str


@dataclass(frozen=True)
class CertRequest:
    model_id: str
    waxal_macro_wer: float
    afrobench_lite_accuracy: float
    bias_corrected_judge_score: float
    mean_fertility_premium: float
    harness_pins: dict[str, str] = field(default_factory=dict)
    weights_yaml: str = ""


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class AfrevalClient:
    def __init__(self, scorer_bin: Path | None = None, base_url: str | None = None, timeout: int = 120):
        """base_url set → API mode; otherwise local scorer mode."""
        self.base_url = base_url
        self.timeout = timeout
        self.scorer = scorer_bin or SCORER
        if not base_url and not self.scorer.exists():
            raise FileNotFoundError(
                f"scorer not built at {self.scorer}; run cargo build --release in afreval-context-score "
                "or pass base_url to use the certification API"
            )

    # ---- API mode (Phase C) ----

    def _api(self, method: str, path: str, body: dict | None = None) -> dict:
        url = f"{self.base_url.rstrip('/')}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def certify_api(self, model_id: str, tokenizer_candidate: str = "",
                    auto_inputs: bool = True, bias_corrected_judge_score: float = 78.0) -> dict:
        """Run the full certification pipeline via the API (auto-inputs)."""
        return self._api("POST", "/v1/certify", {
            "model_id": model_id,
            "weights_yaml": "",
            "tokenizer_candidate": tokenizer_candidate,
            "auto_inputs": auto_inputs,
            "bias_corrected_judge_score": bias_corrected_judge_score,
        })

    def security_report(self) -> dict:
        return self._api("GET", "/v1/security")

    def compliance(self) -> dict:
        return self._api("GET", "/v1/compliance")

    # ---- local scorer mode ----

    def score(self, report: dict, weights_yaml: str) -> dict:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as rf, \
             tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as wf:
            rf.write(_canonical(report))
            wf.write(weights_yaml)
            rpath, wpath = rf.name, wf.name
        try:
            r = subprocess.run(
                [str(self.scorer), "score", "--report", rpath, "--weights", wpath],
                capture_output=True, text=True,
            )
        finally:
            Path(rpath).unlink(missing_ok=True)
            Path(wpath).unlink(missing_ok=True)
        if r.returncode not in (0, 1):
            raise RuntimeError(r.stderr)
        return json.loads(r.stdout)

    def certify(self, req: CertRequest) -> Cert:
        report = {
            "model_id": req.model_id,
            "harness": req.harness_pins,
            "linguistic_fidelity": {
                "waxal_macro_wer": req.waxal_macro_wer,
                "afrobench_lite_accuracy": req.afrobench_lite_accuracy,
            },
            "cultural_safety": {"bias_corrected_judge_score": req.bias_corrected_judge_score},
            "structural_economics": {"mean_fertility_premium": req.mean_fertility_premium},
        }
        scored = self.score(report, req.weights_yaml)
        cert = {
            "model": req.model_id,
            "report": report,
            "score": scored,
            "cert_sha256": hashlib.sha256(_canonical({"model": req.model_id, "score": scored}).encode()).hexdigest(),
        }
        return Cert(
            model_id=req.model_id,
            vertical=scored["vertical"],
            context_score=scored["context_score"],
            linguistic_fidelity=scored["vectors"]["linguistic_fidelity"],
            cultural_safety=scored["vectors"]["cultural_safety"],
            structural_economics=scored["vectors"]["structural_economics"],
            pass_=scored["pass"],
            cert_sha256=cert["cert_sha256"],
        )


__all__ = ["AfrevalClient", "Cert", "CertRequest"]
