---
type: source
tags: [source, implementation-research, blueprint]
updated: 2026-07-31
---

# Source: Milimo AfrEval Implementation Research

**Path:** `dev-docs/Milimo AfrEval Implementation Research.md` (immutable raw source — never edited)

## What this document is

The **architectural and strategic blueprint** that preceded the [Implementation Bible](implementation-bible.md) (per the Bible's closing note: "Original AfrEval architectural blueprint, provided by Mainza"). It establishes the *why* — the epistemological crisis of global AI in African ecosystems — and the strategic business case, in polished proposal form with 42 cited sources.

## Structure

1. **The epistemological crisis** — [tokenization fertility / African Language Tax](../concepts/african-language-tax.md) (with the frontier-model premium table), and the [illusion of pairwise accuracy / evaluation bias](../concepts/llm-as-judge-bias.md) (with the 43% acceptance-rate gap).
2. **The substrate** — [WAXAL](../substrates/waxal.md) multi-modal acoustic modeling, [AfroBench](../substrates/afrobench.md) cross-task fairness, and the [mathematical quantification of code-mixing](../concepts/code-mixing.md) (CMI, I-index, M-index).
3. **The Context Score methodology** — [Linguistic Fidelity × Cultural Safety × Structural Economics](../concepts/context-score.md), per-industry weighting, threshold-based deployment blocking.
4. **Infrastructure** — [zero-trust sandboxing](../concepts/zero-trust-sandboxing.md), kernel isolation, the [Model Context Protocol & four defensive seams](../infrastructure/mcp-execution-boundary.md), [network topology realism](../infrastructure/network-topology.md).
5. **Policy integration** — [AU Continental AI Strategy & sovereign compliance](../strategy/regulatory-landscape.md).
6. **Business** — the [enterprise SaaS tollbooth model & VC alignment](../strategy/enterprise-saas.md) (Norrsken22, Google AI Futures Fund).

## Notable numbers carried into the wiki

- WAXAL: ~1,250h ASR, 235+h TTS, 24 Sub-Saharan languages, 100M+ speakers; 38.0% vs 64.9% macro-WER (fine-tuned edge vs zero-shot).
- Premiums up to ~8.9× (N'Ko) / ~9.3× (Ethiopic); ~11% effective context window.
- 90%+ pairwise accuracy coexisting with up to 43% acceptance-rate gap.
- AU strategy: $1.5T AI economy by 2030; $250–500B needed vs ~$100–150M committed.

## Related

- [Source: Implementation Bible](implementation-bible.md) — the build spec derived from this blueprint
- [Synthesis](../synthesis.md) — discrepancies between the two docs
