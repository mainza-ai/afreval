# afreval-onprem

Air-gapped certification + security-dashboard desktop client for Milimo AfrEval.
**Tauri 2** (Rust core + web frontend), Phase 5 — this is the skeleton, built
now per the [Tauri adoption decisions](../wiki/reports/tauri-integration.md).

## What's here

- **Embedded Rust core** — links `afreval-context-score` (deterministic Context
  Score scorer) and `afreval-airlock` (four-seam tool-call validator) directly
  as crates; no process boundary, bit-identical scores guaranteed.
- **Tauri commands** (exposed to the frontend via `invoke`):
  - `score_report(reportJson, weightsYaml)` → Context Score verdict
  - `validate_tool_call(callJson, policyJson)` → airlock verdict
  - `clearance_status()` → trust-root state (Stronghold vault is post-MVP)
- **Static frontend** (`src/`) — thin shell wiring the commands; the real
  dashboard UI reuses `afreval-dashboard` (build-target-agnostic per decision).

## Run (dev)

```bash
npm install
npm run tauri dev
```

`cargo check` in `src-tauri/` verifies the embedded-crate wiring compiles.

## Design constraints (report §10)

- Air-gapped: local assets only, no `dangerousRemoteUrlIpcAccess`, CSP enforced.
- Local MCP server: **post-MVP** — all tool execution is airlock-gated from day
  one so that server is a thin wrapper later, not a refactor.
- Linux targets: Ubuntu LTS (.deb + AppImage) primary, Debian secondary; declare
  `webkit2gtk-4.1`; Windows day-one for the banking tier.
- Security dashboard ships in the same release, cert-first (§3.5).

## Layout

```
src-tauri/src/lib.rs  # commands (score / validate / clearance)
src-tauri/Cargo.toml  # tauri + afreval-context-score + afreval-airlock
src/                  # static frontend shell
```

## Related

- [Tauri integration report](../wiki/reports/tauri-integration.md)
- [Context Score](../wiki/concepts/context-score.md)
- [agent-airlock subsystem](../wiki/subsystems/agent-airlock.md)
