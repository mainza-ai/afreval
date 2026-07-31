# Milimo AfrEval

Autonomous, context-aware alignment & benchmarking infrastructure for AI in Africa. An enterprise "tollbooth" API layer that routes every AI agent through a certification pipeline before it touches a production database — issuing a **Context Score** that guarantees the model is linguistically accurate, culturally safe, economically viable, and functionally secure inside a zero-trust sandbox.

Built on the generalized **Karpathy Loop** (frozen harness → mutable artifact → instruction file → metric → budget), with every subsystem — tokenizer search, Context Score calibration, BiasScope probing, edge ASR, execution-boundary hardening, compliance — running as an autonomous loop over three frozen data substrates: WAXAL, AfroBench, and afri-fertility.

## Repository structure

```
afreval/
├── wiki/          # the knowledge base — start at wiki/home.md
├── dev-docs/      # raw source documents (immutable)
├── autoresearch/  # vendored karpathy/autoresearch — flattened for re-engineering
├── AfroBench/     # vendored McGill-NLP/AfroBench — flattened for re-engineering
│   └── lm-evaluation-harness/   # git submodule (EleutherAI)
└── afri-fertility/               # vendored CipherSenseAI/afri-fertility — flattened
```

- **`wiki/`** — a persistent, LLM-maintained knowledge base following the [LLM Wiki pattern](wiki/AGENTS.md): interlinked concept, substrate, subsystem, infrastructure, strategy, and build-plan pages, plus a content `index.md`, an activity `log.md`, and an evolving `synthesis.md` of cross-source discrepancies and open questions.
- **`dev-docs/`** — the source of truth: the Implementation Bible (build spec), the Implementation Research blueprint, and the African Language Tax paper.
- **Substrate repos** — upstream clones are **flattened into the tree** (their `.git` history removed) so the Karpathy-loop artifacts (`train.py`, `prepare.py`, `program.md`) can be modified and committed in-repo during AfrEval implementation.

## Cloning

The only remaining submodule is `AfroBench/lm-evaluation-harness` (EleutherAI/lm-evaluation-harness, pinned to upstream HEAD `f4d4b3de` — byte-identical to the previously vendored copy):

```bash
git clone --recursive https://github.com/mainza-ai/afreval.git
```

To update it to a newer upstream:

```bash
git -C AfroBench/lm-evaluation-harness fetch origin
git -C AfroBench/lm-evaluation-harness checkout <new-sha>   # or: git submodule update --remote
```

To pull upstream changes into a flattened repo:

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
- [Build plan](wiki/build-plan/phases.md) — Phase 0–5 roadmap
- [Risk register](wiki/build-plan/risk-register.md) — known risks and mitigations
