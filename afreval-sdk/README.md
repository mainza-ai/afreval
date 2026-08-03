# afreval-sdk

Client SDKs for Milimo AfrEval. Python (working, calls the local certification
pipeline + Rust scorer) and TypeScript (client API shape for the SaaS surface
once live).

## Python

```python
from afreval_sdk import AfrevalClient

client = AfrevalClient()
cert = client.certify(
    "my-model",
    waxal_wer=0.38,
    accuracy=0.62,
    judge_score=78.0,
    premium=2.68,
    pins={...},
    weights_yaml=open("afreval-context-score/weights/telco.yaml").read(),
)
print(cert.context_score, cert.pass_, cert.cert_sha256)
```

Wraps `afreval-context-score` (the deterministic Rust scorer) — same bit-identical
guarantee, same auditability (each cert carries a sha256). This is the
certification path the SaaS API will serve.

## TypeScript

`typescript/src/client.ts` — the typed client surface for the future API
(`certify`, `score`, `securityReport`). Not wired to a live endpoint yet; it
gates on the certification API being served (Phase 5).

## Layout

```
python/    # afreval_sdk package + tests (deterministic, offline)
typescript/  # client shape + types
```

## Related

- [Certification pipeline](../afreval-harness/scripts/certify.py)
- [Context Score](../wiki/concepts/context-score.md)
- [Enterprise SaaS](../wiki/strategy/enterprise-saas.md)
