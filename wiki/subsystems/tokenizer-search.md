---
type: subsystem
tags: [tokenizer, vocab-search, karpathy-loop, BPE, §3.1]
updated: 2026-07-31
---

# Subsystem §3.1 — Tokenizer & Vocab Search Loop

Kills the [African Language Tax](../concepts/african-language-tax.md) at the root by searching for tokenizers that don't over-tax African languages. The closest 1:1 reuse of the original training-style autoresearch loop.

| Field | Spec |
|---|---|
| **Frozen harness** | `harness/tokenizer_eval.py` — loads pinned FLORES-200+/SIB-200/MAFAND-MT corpora, re-tokenizes with candidate vocab, computes CPT/BPT per language and per script (**Latin/Ge'ez/N'Ko stratified, never aggregated blind**) |
| **Mutable artifact** | `candidates/tokenizer_candidate.py` — vocab construction: BPE merge ordering, script-aware pre-tokenization, unigram vs BPE choice, vocab size, byte-fallback thresholds |
| **Instruction file** | `program.md`: *"minimize mean fertility premium vs English across the pinned 20-language/3-script table without regressing English CPT by more than 5%. N'Ko and Ethiopic premiums are scored independently — a win on Latin script does not offset a regression on either."* |
| **Metric** | Mean fertility premium, **script-stratified** (three numbers, not one) |
| **Budget** | Fixed wall-clock per candidate build + re-tokenize + score pass (GPU-bound for large candidate vocabs, CPU-bound for smaller — budget both paths) |
| **Loop flavor** | Training-style (base autoresearch pattern) |
| **Language** | Python |
| **Repo** | `afreval-tokenizer-research` |

## Design notes

- The **script-stratified metric** is the anti-corner-cut device: a Latin-only win must not offset an N'Ko or Ethiopic regression.
- The harness is the frozen scoring ground truth from §2.3 — the [afri-fertility](../substrates/afri-fertility.md) substrate corpora (FLORES-200+, SIB-200, MAFAND-MT).
- **Open parameter:** the "pinned 20-language/3-script table" vs afri-fertility's 23-language/5-tier coverage — reconcile at Phase 0 ([Synthesis](../synthesis.md)).

## Related

- [African Language Tax](../concepts/african-language-tax.md) — the phenomenon being minimized
- [afri-fertility substrate](../substrates/afri-fertility.md) — the measurement engine
- [Context Score — Structural Economics](../concepts/context-score.md) — why this matters commercially
- [Karpathy Loop](../concepts/karpathy-loop.md) — loop flavor
- [Phases — Phase 1 & 3](../build-plan/phases.md)
