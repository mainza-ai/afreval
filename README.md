# Milimo AfrEval

Autonomous, context-aware alignment & benchmarking infrastructure for AI in Africa. An enterprise "tollbooth" API layer that routes every AI agent through a certification pipeline before it touches a production database — issuing a **Context Score** that guarantees the model is linguistically accurate, culturally safe, economically viable, and functionally secure inside a zero-trust sandbox.

Built on the generalized **Karpathy Loop** (frozen harness → mutable artifact → instruction file → metric → budget), with every subsystem — tokenizer search, Context Score calibration, BiasScope probing, edge ASR, execution-boundary hardening, compliance — running as an autonomous loop over three frozen data substrates: WAXAL, AfroBench, and afri-fertility.

## Implementation status

**All 11 target repos have in-tree presence** (all pushed to this repo). Remaining work is operational, not scaffold: Stage B train pull, live BiasScope run, compliance citation sourcing, and the server-side isolation tiers (gVisor/Firecracker/Envoy).

| Area | Repo | Status |
|---|---|---|
| Phase 0 — frozen harnesses | `afreval-harness/` | ✅ **COMPLETE** — all three pins frozen; WAXAL QA pass 2 finished (74,400 clips) with 2,255 drops applied → **QA-approved corpus 72,145 clips / 18 languages** checksummed |
| Phase 1 — Context Score core | `afreval-context-score/` | ✅ Deterministic Rust scorer (bit-identical repeated runs — the acceptance criterion) + deterministic certification pipeline with auditable sha256 certs |
| Phase 1 — tokenizer search | `afreval-tokenizer-research/` | ✅ §3.1 search loop with trained BPE candidates; **script-aware candidate PASSES** (Ethiopic premium 7.83→3.38 at zero English-CPT regression) |
| Phase 2 — execution boundary | `afreval-airlock/` | ✅ Four defensive seams incl. JWS HS256 clearance; §3.5 red-team hardening loop — **19 regression tests, 0 bypasses** |
| Phase 2 — evaluation bias | `afreval-biasscope/` | ✅ §3.3 probe loop (mock/omlx judge backends; acceptance-rate-gap metric) |
| Phase 2 — compliance | `afreval-compliance/` | ✅ §3.6 citation-currency loop (Kenya ODPC + Nigeria NDPC verified current) |
| Phase 4 — edge ASR | `afreval-waxal-net/` | ✅ Loop scaffolding + **zero-shot baseline 41.0% macro-WER**; fine-tuning gates on Stage B train split |
| Phase 4 — field app | `afreval-field-app/` | ✅ Flutter scaffold (elicitation UI + on-device telemetry; needs Flutter SDK to build) |
| Phase 5 — on-prem client | `afreval-onprem/` | 🚧 Tauri 2 skeleton embedding scorer + airlock; trust-root vault + security-dashboard surface (Stronghold, dashboard reuse, local MCP server: post-MVP) |
| Phase 5 — dashboard | `afreval-dashboard/` | ✅ Certification + security web surface (build-target-agnostic) |
| Phase 5 — SDK | `afreval-sdk/` | ✅ Python client SDK (working) + TypeScript client shape (gates on live API) |

**Current status:** Phase 0 **closed** (all harnesses frozen, WAXAL QA-approved at 72,145 clips). Phases 1–2 core built; Phase 4 WAXAL-NET scaffolding live (baseline 41.0% macro-WER to beat).

## Repository structure

```
afreval/
├── wiki/                     # LLM-maintained knowledge base — start at wiki/home.md
├── dev-docs/                 # raw source documents (Implementation Bible, Research blueprint)
├── afreval-harness/          # Phase 0 frozen harnesses + WAXAL acquisition/QA tooling
├── afreval-context-score/    # Rust Context Score scorer + weights/{telco,banking}.yaml
├── afreval-tokenizer-research/  # §3.1 tokenizer search loop + BPE candidates
├── afreval-airlock/          # four-seam tool-call validator + hardening loop
├── afreval-biasscope/        # §3.3 judge-bias probe loop
├── afreval-compliance/       # §3.6 citation-currency loop
├── afreval-onprem/           # Tauri 2 air-gapped client (skeleton)
├── afreval-dashboard/        # certification & security dashboard
├── autoresearch/             # vendored karpathy/autoresearch — flattened for re-engineering
├── AfroBench/                # vendored McGill-NLP/AfroBench — flattened
│   └── lm-evaluation-harness/  # git submodule (EleutherAI)
└── afri-fertility/           # vendored CipherSenseAI/afri-fertility — flattened
```

## Cloning

The only remaining submodule is `AfroBench/lm-evaluation-harness` (EleutherAI/lm-evaluation-harness, pinned to upstream HEAD `f4d4b3de`):

```bash
git clone --recursive https://github.com/mainza-ai/afreval.git
```

To pull upstream changes into a flattened substrate repo:

```bash
git -C autoresearch remote add upstream https://github.com/karpathy/autoresearch
git -C autoresearch fetch upstream && git -C autoresearch merge upstream/main
```

## The three-layer pattern

| Layer | Where | Owned by |
|---|---|---|
| Raw sources | `dev-docs/` + vendored substrate repos | Human (immutable) |
| The wiki | `wiki/` | LLM agent (maintained via ingest/query/lint per `wiki/AGENTS.md`) |
| The schema | `wiki/AGENTS.md` | Human + LLM (co-evolved) |

## Navigation

- [Wiki home](wiki/home.md) — overview and full index
- [Build plan](wiki/build-plan/phases.md) — Phase 0–5 roadmap with live status
- [Risk register](wiki/build-plan/risk-register.md) — known risks and mitigations
- [Repository layout](wiki/build-plan/repository-layout.md) — the eleven planned repos
