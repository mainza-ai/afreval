---
type: substrate
tags: [afri-fertility, tokenization, fertility, cost, metrics, frozen-harness]
updated: 2026-07-31
---

# afri-fertility

The **tokenization economics substrate** for AfrEval — the open measurement engine behind *The African Language Tax* paper, the [Token Fertility Leaderboard](https://datalens.africa/token-fertility-leaderboard), and DataLens Africa's cost-calculator widget. Vendored in-repo at `../afri-fertility/` (flattened).

- **Package:** `afri-fertility` on PyPI. **Pin the exact version before building against it** — treat PyPI version drift as a breaking-change risk, not a routine bump.
- **License:** Apache-2.0 · © 2026 DataLens Africa Research. Python 3.11+, CPU-only, key-free core.
- **Grounding paper:** *The African Language Tax*, [arXiv 2606.24460](https://arxiv.org/html/2606.24460). First to translate the fertility gap into enterprise cost/latency/context terms — exactly the framing the [Structural Economics vector](../concepts/context-score.md) needs.

## Metrics (computed on parallel corpora, isolating language effect)

| Metric | Formula | Meaning |
|---|---|---|
| Fertility `F(L,T)` | tokens / words | Tokens per word. Lower = more efficient. |
| Premium `P(L,T)` | `F(L,T) / F(eng,T)` | ×-more tokens vs English |
| CPT | chars / tokens | Characters packed per token |
| BPT | utf8_bytes / tokens | Bytes per token (cross-script fair) |
| Context efficiency | window_size × CPT | Effective real chars in a fixed context window |

Aggregation is **sum-then-divide** (not mean-of-ratios) with bootstrap 95% CIs; baseline English; NFC normalization.

## Coverage

- **Languages:** 23 across 5 tiers — Core (6: Yoruba, Hausa, Igbo, Wolof, Swahili, Amharic), Latin breadth (11), Non-Latin (3: Tigrinya, Hausa-Ajami, N'Ko), Control (1: Afrikaans), Baselines (2: English, French).
- **Tokenizers:** 14 — tiktoken (o200k_base, o200k_harmony, cl100k_base), HF-gated (Llama-3.1, Llama-4, Gemma-4, Qwen3, DeepSeek-v3, BLOOM, aya-expanse, tekken), API count-only (Claude, Gemini). Unavailable tokenizers are skipped with a warning, never crash a run.
- **Corpora:** FLORES-200, SIB-200, MAFAND-MT (all open-licensed) + custom JSONL/CSV.

## CLI / API surface

`measure` (tokens/fertility/CPT/BPT) · `cost` (widget backend, FX-aware, e.g. USD/NGN/ZAR/KES) · `run` (full locked study from YAML config) · `figures` · `leaderboard` (JSON) · `reproduce` (offline reference suite) · `tokenizers list` / `corpora list` / `languages list`. Full study config, price/FX snapshots, and tokenizer versions recorded in `runs/main/manifest.json`.

## Privacy & security posture (the bar for the whole platform)

The paper states the tool **"stores no user data and makes no network requests beyond downloading tokenizer files from the Hugging Face Hub."** The Bible flags this as the reasonable minimum privacy posture to hold *the entire AfrEval platform* to, not just this component.

**License/compliance caveats:** confirm license compatibility with enterprise SaaS terms before redistributing derived scores publicly (a public token-fertility leaderboard feature needs its own license review). And audit HF Hub egress against on-prem/localization requirements per jurisdiction — a component isn't sovereign-safe just because it's open-source ([regulatory landscape](../strategy/regulatory-landscape.md), [risk register](../build-plan/risk-register.md)).

## Related

- [African Language Tax](../concepts/african-language-tax.md) — the phenomenon it measures
- [Tokenizer search subsystem](../subsystems/tokenizer-search.md) — the loop that attacks the tax at the root
- [Context Score — Structural Economics](../concepts/context-score.md)
- [Synthesis](../synthesis.md) — 20 vs 22 vs 23 language corpus discrepancy
