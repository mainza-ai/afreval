# afreval-dashboard

Enterprise certification & security dashboard (Phase 5 SaaS surface). This is
the web surface enterprise clients look at — the **build-target-agnostic**
frontend that the `afreval-onprem` Tauri client mounts as its UI (per the
[Tauri adoption decisions](../wiki/reports/tauri-integration.md) §10: keep the
frontend build-target-agnostic so the desktop shell is a packaging exercise).

## What it shows

- **Certification** — Context Score results from `afreval-harness/certs/*.cert.json`
  (score, three vectors, pass/fail, cert sha256).
- **Security** — per-seam airlock bypass rates from
  `afreval-airlock/attack/report.json` (never aggregated across seams).
- **Clearance** — trust-root / vault state (on-prem client).

## Data flow

The page renders a single `state.json`. `scripts/export_state.js` (Node, no deps)
assembles it from the artifacts:

```bash
node scripts/export_state.js
python3 -m http.server 8788      # or mount the same UI in afreval-onprem
open http://localhost:8788
```

The same UI is served in-app by the `afreval-onprem` Tauri commands
(`security_report`, `clearance_status`, `score_report`) — this directory is the
reference implementation of that surface.

## Layout

```
index.html + app.js   # single-page dashboard (vanilla, no build step)
scripts/export_state.js  # aggregates certs + security report -> state.json
```

## Related

- [Tauri integration report](../wiki/reports/tauri-integration.md)
- [Enterprise SaaS & VC](../wiki/strategy/enterprise-saas.md)
- [Phase 5](../wiki/build-plan/phases.md)
