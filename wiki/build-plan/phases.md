---
type: build-plan
tags: [phases, milestones, roadmap, plan]
updated: 2026-07-31
---

# Phased Build Plan

Six phases with explicit gates and acceptance criteria. The through-line: **nothing downstream starts until the harness is frozen and versioned.**

## Phase 0 — Harness freeze (weeks 1–3)

**Status: WAXAL QA pass 2 running.** `afreval-harness/` in-tree: pins, `tokenizer_eval.py`, `waxal_eval.py`, `afrobench_eval.py`, acquisition/freeze/bump scripts, checksums frozen for afri-fertility + AfroBench-LITE. WAXAL Stage A eval-split acquisition complete (**76,107 rows, 19 configs, 0 empties**); the §2.1.1 QA pass 2 runs **Ethio-ASR + Sunbird** (WAXAL-tuned ASRs — general zero-shot ASRs fail on spontaneous WAXAL audio, which *empirically reproduces the WAXAL-NET thesis*); Ethio pass done, Sunbird ~13h. Remaining: Sunbird QA → review `qa2_summary.json` flags → drop high-divergence rows → `freeze_checksums.py --pin waxal.yaml` ([waxal.md](../substrates/waxal.md)).

Pin exact versions of [WAXAL](../substrates/waxal.md), [AfroBench(-LITE)](../substrates/afrobench.md), and [afri-fertility](../substrates/afri-fertility.md). Build `harness/` for each as read-only, checksummed artifacts. For WAXAL this is not complete until the §2.1.1 four-step acquisition/QA task list has run end-to-end and its provenance record committed — **a raw, un-audited pull does not satisfy the gate.**

**Acceptance:** harness repo tagged `v0.1.0`, checksums committed, documented procedure for pin bumps (WAXAL and AfroBench are active projects — an unplanned silent bump invalidates historical Context Scores). WAXAL per-language pre/post-filter row counts and edit-distance QA results present in the harness README.

## Phase 1 — Tokenizer & Context Score core (weeks 3–8)

**Status: complete (deterministic half).** `afreval-context-score` (Rust, bit-identical repeated runs ✓ — the acceptance criterion), `afreval-tokenizer-research` (§3.1 loop: mutable candidate artifact, runner, program.md; **script-aware candidate PASSES** — Ethiopic premium 7.83→3.38 at zero English-CPT regression), harness→scorer report bridge, and the **§3.2.1 certification pipeline** (`scripts/certify.py` — deterministic, auditable certs with sha256). The *autonomous* search/calibration variants are Phase 3 by design.

Build [§3.1 tokenizer search](../subsystems/tokenizer-search.md) and the **deterministic (non-search) half** of [§3.2](../subsystems/context-score-calibration.md) — the Rust scorer that takes a fixed weight config and produces a Context Score, *before* the calibration search loop exists. Ship as an invocable, auditable pipeline first; the autonomous calibration loop is Phase 3.

**Acceptance:** given a pinned model + pinned weight config + pinned harness, the scorer produces a **bit-identical score on repeated runs**. ✓ (verified: byte-identical CLI output + cert sha256).

## Phase 2 — Isolation & MCP boundary (weeks 6–12, overlapping Phase 1)

**Status: software seams done; server infra pending.** `afreval-airlock` (Rust) implements all **four** defensive seams — deny-by-default allowlist, ghost-arg stripping/schema, output sanitization (PII+cap), and **seam 4 per-call reauthorization (JWS HS256 clearance — the genuinely-unbuilt upstream piece)** — plus the §3.5 hardening loop (attack program → per-seam bypass rate; **0 bypasses, 19 regression tests**). Still to stand up (server infra, not laptop-testable): [gVisor](../infrastructure/isolation-tiers.md) + Firecracker tiers and Envoy credential injection.

Stand up the [gVisor tier](../infrastructure/isolation-tiers.md), Firecracker tier, Envoy credential injection, and fork/extend [agent-airlock](../subsystems/agent-airlock.md) for the fourth seam (per-call reauthorization). Infrastructure, not research — **no autonomous loop yet, just build it correctly.**

**Acceptance:** a known-hostile test agent (deliberately built to attempt privilege escalation, ghost-arg injection, credential exfiltration) is **blocked on all three implemented seams** in a controlled red-team pass, logged and reproducible.

## Phase 3 — Autonomous loops go live (weeks 10–20)

Bring up §3.1's search variant, §3.2's calibration loop, [§3.3 BiasScope](../subsystems/biasscope.md), and §3.5's adversarial hardening loop, in that order — each gated on the corresponding Phase 1/2 deterministic component being stable. Every run produces a log (SeeleAI/Thoth "durable runs, visible ledgers, reviewable verdicts" pattern); a **human reviews and approves** before any loop output changes a production weight config or ships a regression test.

**Acceptance:** each loop has run to **at least 50 iterations** against its metric with a documented improvement trajectory (or a documented plateau reason), and a human sign-off log exists for every kept change that reached production.

## Phase 4 — WAXAL-NET edge loop + field app (weeks 16–26)

Requires the MLX/ONNX-mobile fork lineage ([platform caveat](../concepts/karpathy-loop.md)). Build the Dart/Flutter field app in parallel — it depends only on the WAXAL image-prompted-elicitation methodology, not on the training loop finishing.

**Acceptance:** a fine-tuned edge model **beats the relevant zero-shot foundation-model baseline on macro-WER over the 19-language WAXAL-NET set**, run on hardware comparable to the actual target device class, with the **OOD-generalization secondary metric also reported** (not cherry-picked in-distribution only).

## Phase 5 — Compliance loop + SaaS surface (weeks 20–30)

[§3.6 compliance loop](../subsystems/compliance-loop.md) plus the TypeScript/JavaScript enterprise dashboard, developer SDK, and MCP-based enterprise integrations. **This is the revenue surface — build it last, after the scoring core is trustworthy, not first.**

## Related

- [Risk Register](risk-register.md)
- [Repository Layout](repository-layout.md)
- [Synthesis](../synthesis.md) — open parameters that block Phase 0
