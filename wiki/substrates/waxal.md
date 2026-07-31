---
type: substrate
tags: [waxal, asr, tts, acoustic, dataset, frozen-harness]
updated: 2026-07-31
---

# WAXAL

The **acoustic substrate** for AfrEval — the frozen eval harness for the Linguistic Fidelity vector's speech component and the training substrate for the [WAXAL-NET edge ASR loop](../subsystems/waxal-net.md).

- **Source:** [Waxal-Multilingual/speech-data](https://github.com/Waxal-Multilingual/speech-data) · paper [arXiv 2602.02734](https://arxiv.org/abs/2602.02734) · HF mirror `google/WaxalNLP`
- **Scale:** ~1,250 hours transcribed ASR; ~180–235 hours TTS (hours vary by paper revision — **pin the exact revision**); 21–27 languages depending on release (Research doc says 24 Sub-Saharan languages); 100M+ speakers represented
- **Provenance:** collected via partnerships with Makerere University, University of Ghana, Digital Umuganda, Media Trust, Loud and Clear, and AIMS Senegal — regional institutions, useful for data-sovereignty conversations with African regulators

## Collection methodology (what makes it authentic)

- **Image-prompted speech**: speakers describe an image in their native language — avoids the artificial cadence of scripted reading — captured in natural environments, each clip ≥15 seconds, with speaker age/gender/language/environment metadata tracked.
- Only **~10% of collected audio is transcribed** (by paid local linguistic experts, using local scripts where available) — this is the ASR training/eval set.
- **TTS** portion is studio-quality, single-speaker, phonetically balanced.

## The WAXAL-NET finding (the benchmark to beat)

[WAXAL-NET](https://arxiv.org/abs/2606.02375) confirms AfrEval's core thesis: **fine-tuned compact edge models beat massively multilingual zero-shot foundation models on macro-averaged WER for spontaneous African speech** — 38.0% vs 64.9% on the benchmark's 19-language set — with fine-tuned models generalizing to out-of-distribution speech while zero-shot models only win when the test domain matches their pretraining distribution.

AfrEval integrates **character error rate (CER) alongside WER**: for syllabary-script languages the CER/WER ratio reveals substantially higher character-level accuracy than headline WER suggests. Don't drop CER.

## Use in AfrEval

- **Linguistic Fidelity** (acoustic component): WER/CER against the WAXAL held-out set.
- **WAXAL-NET edge ASR loop** (§3.4): fine-tuning substrate, MLX/ONNX-mobile lineage.
- WAXAL field collection methodology is also the template for AfrEval's own Dart/Flutter [field app](../subsystems/waxal-net.md) (image-prompted elicitation UI).

## §2.1.1 Acquisition & QA task list (Phase 0 blocking, agent-executable)

**Hub ground truth (verified 2026-07-31, repo sha `e0a62aa`):** `google/WaxalNLP` is organized per-language, per-task as configs (`{lang}_asr`, `{lang}_tts`). Each `_asr` config ships **labeled splits `train`/`validation`/`test`** — every row carries a `transcription` field — plus a large **`unlabeled`** split whose rows have `transcription == ""`. So transcribed-vs-untranscribed is separated **by split**, not by a filter inside the labeled data: the paper's "~10% of collected audio was transcribed" describes pre-release collection; the untranscribed remainder ships on the Hub as the `unlabeled` split. 19 languages publish an `_asr` config.

**Acquisition strategy: two-stage, eval-first.** The full ~1,250h pull (~52 days at observed Hub transfer rates) buys nothing for the Phase 0 gate — the harness only scores the **held-out eval split** (§3.4: "WAXAL held-out eval split"). Stage A (Phase 0): acquire `validation`+`test` only (~2% of the collection, ~1–2 days), QA, freeze. Stage B (Phase 4): pull labeled `train` on-demand as the WAXAL-NET fine-tuning substrate. The `unlabeled` split is **never** acquired (pretraining-only).

**Stage A status: QA-BLOCKED (2026-07-31).** Acquisition itself is complete and clean — all 19 `_asr` configs, `validation`+`test`, **76,107 rows, 0 empty transcriptions**, ~21GB audio materialized and decode-verified. **However, the QA second-ASR pass found a corpus-level anomaly:** sampled clips across all 19 languages are 33–68% silent with sparse periodic broadband pulses and clean −80dB background — *not continuous speech* — and Whisper (both ctranslate2 and MLX implementations) fully degenerates on them while transcribing known-good English perfectly (confirmed via a local Qwen3.6-35B VLM spectrogram analysis + quantitative scan). The audio does not appear to match its long image-description transcriptions (the same failure class the `galsenai/WaxalNLP` fork reported). **The WAXAL harness must not be frozen on trust** — a human/linguist listening check and corpus-source investigation are required before freezing. See [synthesis](../synthesis.md) and the pin's `qa_findings`.

**Loader caveat:** `datasets.load_dataset()` materializes the *whole* config (including `unlabeled` shards) even for one split — it must not be used for acquisition. `acquire_waxal.py` uses scoped `snapshot_download` + pyarrow reads instead.

1. **Pull by config, requested splits only.** For each pinned language: `load_dataset("google/WaxalNLP", "{lang}_asr", split="validation+test")`, or `snapshot_download(... allow_patterns="data/ASR/*/*-{train,validation,test}-*.parquet")` — **never** `*-unlabeled-*` shards; TTS configs excluded unless a subsystem needs them. A blind `tree/main` clone is forbidden.
2. **Materialize + verify audio.** Decode each clip; corrupt/unreadable audio raises and never enters the harness (replicates the `galsenai/WaxalNLP` fork's exclusion of unreadable files). Confirm empties are (near-)absent in labeled splits; filter only if a config's rate is non-trivial (>0.1%).
3. **QA pass — the real filter.** Re-transcribe with a second ASR pass, compute edit distance against the shipped transcription per clip, flag/drop high-divergence rows (`harness.waxal_eval` provides deterministic WER/CER).
4. **Checksum and freeze.** Checksum the filtered corpus; commit as the Phase 0 harness artifact. Record the HF revision (`e0a62aa…`), language codes, and per-language pre/post-filter row counts in the harness README — the provenance record that makes a Context Score defensible.

Implemented in `afreval-harness/scripts/acquire_waxal.py` (default splits `validation test`; `--splits train validation test` for Stage B; dry-run resolves the 19 configs from the dataset card).

## Related

- [AfroBench](afrobench.md) — the textual half of Linguistic Fidelity
- [WAXAL-NET subsystem](../subsystems/waxal-net.md) — the edge fine-tuning loop built on this substrate
- [Context Score](../concepts/context-score.md) — Linguistic Fidelity vector
- [Phases — Phase 0](../build-plan/phases.md) — harness freeze gate
- [Synthesis](../synthesis.md) — language/hour count discrepancies to pin
