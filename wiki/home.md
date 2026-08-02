---
type: overview
tags: [afreval, home, milimo]
updated: 2026-07-31
---

# Milimo AfrEval — Wiki Home

A structured, persistent knowledge base for **Milimo AfrEval**: the autonomous, context-aware alignment & benchmarking infrastructure for AI in Africa. This wiki compiles the project's two source documents — the [Implementation Bible](sources/implementation-bible.md) (the build spec) and the [Implementation Research](sources/implementation-research.md) (the strategic blueprint) — into interlinked pages that stay current as the project evolves.

## What the project is

Milimo AfrEval is an enterprise **"tollbooth" API layer** for AI deployment in Africa. Before a sovereign government or corporate entity lets an AI agent touch a production database, the model is routed through the AfrEval pipeline, which tests it against proprietary, localized African datasets and issues a certified **Context Score** — a 0–100 composite guaranteeing the model is linguistically accurate, culturally safe, economically viable, and functionally secure inside a zero-trust sandbox.

Three failure modes motivate it ([Research](sources/implementation-research.md)):
- **Tokenization fertility** — African languages cost 1.7×–3.3× more tokens than English (up to ~9× for N'Ko), an economic "African Language Tax" ([african-language-tax](concepts/african-language-tax.md)).
- **Evaluation bias** — LLM-as-judge systems show up to a 43% acceptance-rate gap across languages that pairwise accuracy is blind to ([llm-as-judge-bias](concepts/llm-as-judge-bias.md)).
- **Execution insecurity** — cyber-capable agents must be tested in genuinely air-gapped sandboxes ([zero-trust-sandboxing](concepts/zero-trust-sandboxing.md)).

## The design substrate

The whole system is built on the **Karpathy Loop** ([concepts/karpathy-loop.md](concepts/karpathy-loop.md)): a frozen harness, a single mutable artifact, a human-authored instruction file, one scalar metric, and a fixed budget — iterated by an autonomous agent overnight. AfrEval's insight is that *every* subsystem — not just ML training — can be a Karpathy Loop.

It scores against three frozen, never-modified data substrates:

| Substrate | Domain | Wiki page |
|---|---|---|
| WAXAL | acoustic — ~1,250h transcribed ASR + TTS | [waxal](substrates/waxal.md) |
| AfroBench / AfroBench-LITE | textual & reasoning — 64 languages, 15 tasks | [afrobench](substrates/afrobench.md) |
| afri-fertility | tokenization economics — CPT/BPT/fertility | [afri-fertility](substrates/afri-fertility.md) |

## The six subsystems

Each is a Karpathy Loop with a specified harness / artifact / instruction file / metric / budget:

1. [Tokenizer & vocab search](subsystems/tokenizer-search.md) — kills the African Language Tax at the root
2. [Context Score calibration](subsystems/context-score-calibration.md) — the core IP, weight-search over per-vertical configs
3. [BiasScope adversarial probing](subsystems/biasscope.md) — discover judge-bias blind spots
4. [WAXAL-NET edge ASR fine-tuning](subsystems/waxal-net.md) — compact models beating zero-shot baselines on low-end mobile
5. [agent-airlock hardening](subsystems/agent-airlock.md) — adversarial red-teaming of the execution boundary
6. [Compliance & documentation](subsystems/compliance-loop.md) — keeping regulatory mappings current

## Infrastructure, strategy, build

- [Zero-trust infrastructure](infrastructure/isolation-tiers.md), [MCP execution boundary](infrastructure/mcp-execution-boundary.md), [network topology realism](infrastructure/network-topology.md)
- [Regulatory landscape](strategy/regulatory-landscape.md) (AU Continental AI Strategy, Malabo Convention, Kenya/Nigeria) and the [enterprise SaaS / VC case](strategy/enterprise-saas.md)
- [Phased build plan](build-plan/phases.md), [risk register](build-plan/risk-register.md), [repository layout](build-plan/repository-layout.md)
- Evolving cross-source [synthesis](synthesis.md) — including flagged discrepancies between the two source docs

## Navigation

Start with [index.md](index.md) (content catalog) or [log.md](log.md) (activity timeline). Read [AGENTS.md](AGENTS.md) for the schema and conventions that maintain this wiki.

## Repository status

The workspace lives in the [`mainza-ai/afreval`](https://github.com/mainza-ai/afreval) GitHub repo. **Phase 0 is complete** (all three harness pins frozen; WAXAL QA-approved at 72,145 clips / 18 languages) and **9 of 11 target repos are implemented in-tree** — see [repository-layout](build-plan/repository-layout.md) for the full status table. Structure: `wiki/` (this knowledge base), `dev-docs/` (raw sources), the nine `afreval-*` subsystem repos, and the three substrate repos vendored in-repo — `autoresearch/`, `AfroBench/`, and `afri-fertility/` are **flattened** (no local git history) so their loop artifacts can be re-engineered and committed directly; `AfroBench/lm-evaluation-harness/` is a **git submodule** of EleutherAI/lm-evaluation-harness pinned to upstream HEAD. Clone with `git clone --recursive`. See [README.md](../README.md) for structure and sync commands. This state is current as of the latest [log](log.md) entry.
