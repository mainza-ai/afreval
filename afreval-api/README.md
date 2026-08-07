# afreval-api — the certification HTTP API (Phase C)

The "tollbooth" surface: wraps the deterministic certification pipeline
(`afreval-harness/scripts/certify.py`), the §3.5 security report, and the
§3.6 compliance registry behind versioned HTTP endpoints. Both SDKs
(`afreval-sdk/python`, `afreval-sdk/typescript`) call this.

## Endpoints

| Method | Path | Returns |
|---|---|---|
| GET  | `/v1/health` | liveness + scorer presence |
| POST | `/v1/certify` | deterministic Context Score cert (`model`, `context_score`, `vectors`, `pass_`, `cert_sha256`, `input_sources`) |
| GET  | `/v1/security` | last §3.5 hardening-loop report (per-seam bypass rates) |
| GET  | `/v1/compliance` | §3.6 citation-currency status |

`POST /v1/certify` body:

```json
{
  "model_id": "my-model",
  "tokenizer_candidate": "EfficientRouteCandidate",
  "bias_corrected_judge_score": 70,
  "auto_inputs": true
}
```

`auto_inputs: true` (default) pulls WER from the frozen QA baseline and the
judge from §3.3 bias correction server-side — nothing hand-typed.

## Run

```bash
afreval-harness/.venv/bin/python -m uvicorn api:app --port 8788 \
  --app-dir afreval-api
```

Requires the Rust scorer built (`cargo build --release` in
`afreval-context-score`) for `/v1/certify`.

## Design

- Certification is the deterministic pipeline invocation, never agent-optimized
  (§3.2.1) — the API just calls `certify.py`.
- The security + compliance endpoints read the frozen loop artifacts.
- Versioned (`/v1/*`) so the contract can evolve without breaking clients.
