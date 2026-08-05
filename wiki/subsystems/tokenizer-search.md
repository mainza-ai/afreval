---
type: subsystem
tags: [tokenizer, vocab-search, karpathy-loop, BPE, §3.1]
updated: 2026-08-05
---

# Subsystem §3.1 — Tokenizer & Vocab Search Loop

Kills the [African Language Tax](../concepts/african-language-tax.md) at the root by searching for tokenizers that don't over-tax African languages. The closest 1:1 reuse of the original training-style autoresearch loop.

## Status: Latin-African gap closed (SIB-200 corpus mix)

The prior best candidates ([script-aware](tokenizer-search.md), efficient-route) held Latin premiums at baseline (1.5456) because the BPE training corpus had **no Yoruba/Hausa/Igbo/Swahili text** — they are WAXAL TTS-only. Per §2.3, the SIB-200 corpus is the pinned source for that gap. On 2026-08-05 the loop added SIB-200 African-Latin sentences (6 languages, train+test) to `train_bpe.py`'s corpus mix and retrained (8,000 merges). Result with the efficient-route candidate:

| metric | before | after | Δ |
|---|---|---|---|
| latin premium | 1.5456 | **1.2876** | **−16.7%** |
| ethiopic premium | 3.3770 | **2.8255** | **−16.3%** |
| english_cpt | 5.7349 | 5.7349 | 0.0 (exactly at baseline) |
| verdict | PASS | **PASS** | — |

All five African-Latin reference-suite languages now route to the BPE (yor 0.63×, ibo 0.82×, hau 0.85×, swh 0.93×, fra/eng stay on o200k via min-routing). English CPT is held at baseline by the min() routing. Logged in `results.tsv` (`candidate/bpe-sib200-v0..v4`, merges 500→8000).

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
- **Corpus mix is a live search lever**: `train_bpe.py --sib200-per-lang <n>` adds SIB-200 African-Latin text (FLORES is gated; SIB-200 is open). This closed the Latin-African gap on 2026-08-05.
- **Open parameter:** the "pinned 20-language/3-script table" vs afri-fertility's 23-language/5-tier coverage — reconcile at Phase 0 ([Synthesis](../synthesis.md)).

## Related

- [African Language Tax](../concepts/african-language-tax.md) — the phenomenon being minimized
- [afri-fertility substrate](../substrates/afri-fertility.md) — the measurement engine
- [Context Score — Structural Economics](../concepts/context-score.md) — why this matters commercially
- [Karpathy Loop](../concepts/karpathy-loop.md) — loop flavor
- [Phases — Phase 1 & 3](../build-plan/phases.md)
