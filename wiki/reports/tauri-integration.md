---
type: report
tags: [tauri, rust, dashboard, on-prem, data-sovereignty, decision-input]
updated: 2026-07-31
---

# Tauri Integration Investigation — Report

**Status: ADOPTED (2026-07-31).** Recommendation accepted: Tauri 2 for an air-gapped `afreval-onprem` certification + security-dashboard client (Phase 5). Decisions on the open questions recorded in §10 below. This page remains the decision record until superseded.

## Executive summary

Tauri is a mature, stable framework (v2, GA since Oct 2024) for building **desktop apps with a Rust backend and any web frontend**, using the OS's native webview — no bundled Chromium. It aligns unusually well with three things AfrEval already decided: Rust on the hot path, TypeScript/JavaScript on the surface, and a zero-trust, data-sovereign posture.

**Recommended: adopt Tauri for exactly one new surface — a `afreval-onprem` desktop client** that embeds the `afreval-context-score` Rust scorer directly, reuses the `afreval-dashboard` web frontend, and ships air-gapped for the financial/government tier that must keep evaluation data local (Malabo Convention, Kenya ODPC, Nigeria NDPC). This is a Phase 5 extension, not a rewrite; the SaaS web surface remains the primary revenue path. **Not recommended:** for the field app (stays Flutter), the server-side zero-trust runtime (stays gVisor/Firecracker), or the search loops (stay headless Python/Rust).

## 1. What Tauri is (current state)

- **Backend:** Rust (`tauri` crate). Frontend: any stack that compiles to HTML/JS/CSS (Vite/React, Svelte, Leptos, etc.) via the system webview — WebView2 (Windows), WKWebView (macOS/iOS), WebKitGTK (Linux).
- **Platforms:** Linux, macOS, Windows, **plus Android and iOS** in v2 (native Swift/Kotlin shells; plugin system).
- **Size/perf:** apps as small as ~600KB; low memory; no Node runtime in production; no Chromium bundle (avoids Electron's ~100–150MB floor).
- **Licensing:** core is MIT / Apache-2.0.
- **Distribution:** signed installers (macOS notarization, Windows signing), app stores (incl. Google Play / App Store), AppImage/Snap/Deb/RPM on Linux, CrabNebula Cloud for managed signing + auto-update.

## 2. Tauri's security model (zero-trust alignment)

Tauri's default posture maps directly onto AfrEval's "evaluation sandbox is a target" threat model:

- **Capabilities** — the modern v2 authorization model: IPC access is granted *per window/webview* against declarative permission sets. A window associated with **no capability has no IPC access at all**. This is deny-by-default at the framework level.
- **Permissions + command scopes** — fine-grained allow/deny per command and per resource path (e.g. fs plugin scoped to a directory).
- **CSP + security headers** — enforced via `tauri.conf.json` (`app.security.csp`, `app.security.headers`).
- **Isolation Pattern** — an optional hardening layer: a sandboxed `<iframe>` intercepts all IPC, re-encrypts messages with SubtleCrypto before they reach the Rust core. Directly reusable as a defense-in-depth layer in front of any cert-boundary UI.
- **Stronghold plugin** — encrypted on-disk secure storage (IOTA stronghold). Candidate home for offline JWS clearance key material pinned to an operator trust root (§3.5 seam 4).
- **Caveat:** `dangerousRemoteUrlIpcAccess` exists and is explicitly dangerous (trusts remote domains with IPC). Policy: never use it; the on-prem client loads local assets only.

## 3. Where Tauri fits — fit map against the current plan

| AfrEval surface | Plan (current) | Tauri fit | Verdict |
|---|---|---|---|
| `afreval-context-score` (Rust scorer + Python research) | Rust core, FFI/gRPC | Scorer embeds **directly as a crate** (no sidecar needed); Python research loop stays server/CLI | Strong, but Tauri is not the research loop — it's a *host* for the scorer |
| `afreval-dashboard` (Phase 5 SaaS surface) | TypeScript/JavaScript web | Same frontend can target **both** the SaaS web app and a Tauri desktop shell (Vite builds to web *and* `tauri` dist) | Enabler — frontend reuse is the key architectural win |
| Security dashboard (§3.5) | TS/JS "enterprise clients will actually look at" | Natural fit as a native desktop monitor (airlock bypass rate per seam, clearance state) | Fit |
| On-prem / air-gapped certification tier (banks, govts) | Not yet specified | **This is the missing piece** — a local, offline client that produces Context Scores with zero external egress | **Primary recommendation** |
| `afreval-field-app` (§3.4) | Dart/Flutter mobile | Tauri mobile exists but is newer and less mature than Flutter's mobile story; the spec already fixed Flutter + on-device telemetry | **Do not switch** |
| Zero-trust runtime (§4) | gVisor/Firecracker/Envoy | Server infrastructure, not an app; out of scope for Tauri | Out of scope |
| MCP-based enterprise integrations (Phase 5) | "MCP-based" | Tauri has **no official MCP runtime**. Community projects (`hypothesi/mcp-server-tauri`, `P3GLEG/tauri-plugin-mcp`) are *development tooling* for AI agents to debug Tauri apps — not a production MCP server. Any cert/audit MCP server must be built on AfrEval's own JWS/airlock machinery, not adopted | Build it ourselves; do not rely on community plugins |

## 4. Target architecture — `afreval-onprem` (Phase 5 addition)

```
┌────────────────────────────────────────────────────────┐
│  Tauri 2 desktop app (air-gapped, signed, offline)      │
│                                                        │
│  Frontend (webview, local assets only, CSP enforced)    │
│   └── reuses afreval-dashboard (React/Vite) frontend    │
│         ├── certification UI · score breakdown · plots  │
│         └── security dashboard (per-seam bypass rate)   │
│                                                        │
│  Rust core (tauri commands, capability-gated IPC)       │
│   ├── afreval-context-score  ← embedded crate          │
│   │     (bit-identical Context Score, deterministic)   │
│   ├── afreval-airlock validator ← embedded crate       │
│   │     (JWS clearance / ToolOutputTrustGuard)          │
│   ├── Stronghold vault (JWS key material, trust root)   │
│   └── optional: Python harness sidecar (externalBin,    │
│         pyinstaller-bundled) for afri-fertility runs    │
└────────────────────────────────────────────────────────┘
```

Design principles to carry in:
- **Embed, don't sidecar, the scorer.** The Rust core is already specified as a crate-able hot path; linking it directly keeps the "same model + config + harness → bit-identical score" guarantee and avoids process boundary issues.
- **Sidecars only for Python.** If an on-prem deployment needs the afri-fertility/calibration harness, bundle it via `bundle.externalBin` (pyinstaller'd) and invoke through `tauri-plugin-shell` with scoped permissions. Capability-gate the shell plugin narrowly.
- **Local-first.** No remote assets, no `dangerousRemoteUrlIpcAccess`, auto-update via signed installers or disabled for fully air-gapped clients (side-loadable installers instead).
- **Auditability.** All evaluation runs log locally (append-only, hashed) — the durable-runs/visible-ledger pattern from SeeleAI/Thoth (§5 Phase 3) extends to on-prem.

## 5. MCP angle (AfrEval-specific)

AfrEval certifies agents that speak MCP; a Tauri on-prem client could additionally **host a local MCP server** exposing certification status / audit trail to a customer's internal ops agents — while air-gapped. That is a defensible enterprise feature, but it is **custom work**: the MCP server sits behind `afreval-airlock`'s validation and JWS clearance, and community Tauri-MCP tooling must not be on this security-critical path.

## 6. Alternatives comparison (for the same on-prem/dashboard surface)

| Option | Pros | Cons vs. the plan |
|---|---|---|
| **Tauri 2** | Small, fast, Rust-native (matches scorer/validator), capability/CSP security, web-frontend reuse | Rust learning curve; webview rendering variance across OSes; newer than Electron |
| Electron | Most mature ecosystem; consistent Chromium rendering | ~100–150MB floor; Node main process (off-stack); weaker alignment with the Rust scorer |
| Flutter desktop | Same codebase as the field app (Dart reuse) | Desktop support less mature on macOS/Linux; Rust integration via FFI is more work than Tauri's native core |
| Wails (Go) | Simple, small | Go backend doesn't match the Rust scorer/validator; weaker security machinery |
| Web-only (status quo) | Zero new tooling | No air-gapped/offline path for the data-sovereignty tier; the §3.5 security dashboard stays browser-bound |

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Webview rendering inconsistency (WebView2 vs WKWebView vs WebKitGTK) | Test matrix per OS; charting libs with software fallbacks; pin target: enterprise Windows + macOS first, Linux (govt/mobile operators) second |
| Rust skill constraint on a JS-heavy team | Plan is already Rust-heavy (scorer, airlock) — Tauri adds no *new* language, just UI plumbing |
| Python harness embedding is awkward | Scorer is Rust (embedded natively); Python only via sidecar when required; keep research loop server-side |
| Security audit burden for a new trust surface | Reuse capabilities/Isolation Pattern defaults; no remote content; on-prem client inherits the airlock/JWS machinery rather than adding its own |
| Scope creep (Tauri becomes a second product) | Constrain to one repo + one feature: air-gapped certification + security dashboard; SaaS web remains primary |
| Upstream dependency (tauri crates/plugins) | Pin crate versions; treat tauri release notes as a security feed (same discipline as §3.5 agent-airlock) |

## 8. Phased recommendation

- **Phase 1–4 (status quo):** no Tauri. Build the Rust scorer and the web `afreval-dashboard`; keep the frontend componentized and build-target agnostic so it can later mount inside a Tauri shell without rework.
- **Phase 5:** add repo `afreval-onprem` (Tauri 2, Rust core embedding `afreval-context-score` + `afreval-airlock`; frontend = `afreval-dashboard`). Gate: ships an air-gapped, signed client that reproduces a bit-identical Context Score with zero external egress, and the per-seam security dashboard.
- **Field app:** remains Flutter (mobile maturity). Re-evaluate Tauri mobile only if a unified desktop+mobile codebase ever outweighs Flutter's lead.

## 9. Open questions for the reviewer

1. Is the air-gapped **on-prem certification client** a near-term requirement (customer-driven) or a Phase 5 hedge? If customers are already asking, Tauri moves up in priority.
2. Should the on-prem client include the **security dashboard** (§3.5) from the start, or only certification?
3. Is a **local MCP server** in the on-prem client worth building in Phase 5, or should MCP enterprise integrations remain server-side only?
4. Linux distribution target (WebKitGTK) — which enterprise OSes must be supported for the government tier?

## 10. Decisions (adopted 2026-07-31)

1. **Air-gapped client: strategically core, built in Phase 5 — de-risked now.** Not a hedge (air-gap/on-prem is the top-tier requirement per the [risk register](../build-plan/risk-register.md) and [enterprise SaaS](../strategy/enterprise-saas.md)). From Phase 1–2: keep `afreval-context-score` + `afreval-airlock` crate boundaries clean and the `afreval-dashboard` frontend build-target-agnostic so the desktop shell is a packaging exercise. Package `afreval-onprem` in Phase 5; early customer demand gates on scorer bit-identical/auditable (Phase 1) + airlock seams 1–3 (Phase 2).
2. **Security dashboard: yes, in the same on-prem release — cert-first, dashboard-second.** Reuses the identical embedded airlock telemetry (per-seam bypass rates, JWS clearance state, Phase 3 ledger). No placeholder; it is a credibility surface.
3. **Local MCP server: yes, post-MVP, designed-for from day one.** All tool execution in the on-prem client routes through the embedded airlock validator from the start so the MCP server is a thin wrapper later. Build after the MCP spec/ecosystem stabilizes; sits behind airlock + JWS clearance.
4. **Linux targets: Ubuntu LTS (.deb + AppImage) primary; Debian stable secondary; no RPM in v1.** Declare system `WebKitGTK` (webkit2gtk-4.1) in the .deb and test rendering on target distros (least-consistent webview). Windows supported from day one for the banking tier.

## Sources

- [Tauri 2.0 docs](https://v2.tauri.app/) — architecture, size, security, capabilities, sidecars, distribution
- [Tauri security docs](https://v2.tauri.app/security/) — capabilities, permissions, CSP, Isolation Pattern
- [Tauri sidecar docs](https://v2.tauri.app/develop/sidecar/) — `externalBin`, shell plugin
- [Tauri 2.0 mobile announcement](https://v2.tauri.app/blog/tauri-20) — Android/iOS via Swift/Kotlin shells
- Community MCP: [hypothesi/mcp-server-tauri](https://github.com/hypothesi/mcp-server-tauri), [P3GLEG/tauri-plugin-mcp](https://github.com/P3GLEG/tauri-plugin-mcp) — dev-tooling, not production MCP runtime
- Cross-referenced against [Bible §3.2/§3.5/§5](../sources/implementation-bible.md), [repository layout](../build-plan/repository-layout.md), [regulatory landscape](../strategy/regulatory-landscape.md)
