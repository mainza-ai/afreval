---
type: overview
tags: [log, timeline]
updated: 2026-07-31
---

# Wiki Log

Append-only chronological record of wiki activity. Parseable with `grep "^## \[" log.md | tail -5`.

## [2026-07-31] bootstrap | Initial wiki creation

Created the Milimo AfrEval wiki from the two source documents in `dev-docs/` plus the three substrate repos. Wrote schema, home, index, synthesis, 6 concept pages, 3 substrate pages, 6 subsystem pages, 3 infrastructure pages, 2 strategy pages, 3 build-plan pages, and 2 source pages. Logged flagged discrepancies between sources in `synthesis.md`.

## [2026-07-31] ingest | Milimo_AfrEval_Implementation_Bible.md

Ingested the **Implementation Bible** (v1.0 build spec). Established the Karpathy Loop as the core design pattern, the six-subsystem architecture (§3), infrastructure & trust boundary (§4), phased build plan (§5), and risk register (§6). Wrote source page `sources/implementation-bible.md` and propagated its specifications into all concept, substrate, and subsystem pages.

## [2026-07-31] ingest | Milimo AfrEval Implementation Research.md

Ingested the **Implementation Research** blueprint. Established the epistemological crisis framing (African Language Tax, evaluation bias), the Context Score methodology, zero-trust infrastructure strategy, and the regulatory/SaaS business layer. Wrote source page `sources/implementation-research.md` and propagated its framing into concept and strategy pages.

## [2026-07-31] repo | Initialize & push to GitHub

Initialized the workspace as a git repo (`main`), added origin `https://github.com/mainza-ai/afreval.git`, and pushed the wiki + dev-docs + substrate clones (commit `0d6c6c2`). Initial structure registered `autoresearch`/`AfroBench`/`afri-fertility` as git submodules.

## [2026-07-31] repo | Flatten substrate repos

Per the decision to re-engineer the substrate repos in-place, replaced the three submodules with vendored, flattened content so `train.py`/`prepare.py`/`program.md` edits live in-repo (commit `024346a`). Local git history dropped; repos remain re-clonable from upstream.

## [2026-07-31] repo | Restore lm-evaluation-harness as submodule

`AfroBench/lm-evaluation-harness` (~16k files) converted back to a git submodule of EleutherAI/lm-evaluation-harness, pinned to upstream HEAD `f4d4b3de` — verified byte-identical to the previously flattened tree (commit `4beb0db4`).

## [2026-07-31] docs | README + wiki repo-status update

Created top-level `README.md` (structure, clone/sync commands, three-layer pattern). Updated wiki: substrate location lines, karpathy-loop vendored note, AGENTS.md raw-source layer, home.md repository-status section, repository-layout current-vs-target note, and this log.

## [2026-07-31] report | Tauri integration investigation

Researched Tauri v2 (Rust backend, webview frontend, mobile support, capability/CSP security model, sidecars). Wrote `reports/tauri-integration.md` for human review: recommends adopting Tauri for an air-gapped `afreval-onprem` certification + security-dashboard client in Phase 5, embedding the Rust scorer/validator as crates and reusing the dashboard frontend; explicitly not for the Flutter field app or the server-side zero-trust runtime. Added `reports/` to schema and index.

## [2026-07-31] decision | Adopt Tauri 2 (afreval-onprem)

Human approved Tauri integration. Decisions recorded in report §10: (1) air-gapped client is strategically core, built Phase 5, de-risked from Phase 1–2 via clean crate boundaries + frontend build-target-agnostic; (2) security dashboard included in same on-prem release, cert-first; (3) local MCP server post-MVP, all tool execution airlock-gated from day one; (4) Linux targets Ubuntu LTS (.deb+AppImage) + Debian secondary, no RPM v1, WebKitGTK declared/tested. Added `afreval-onprem` to the target repository layout (now 11 repos).
