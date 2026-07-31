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

1. **Pull by config, not by tree.** For each pinned language: `load_dataset("google/WaxalNLP", "{lang}_asr")` or `snapshot_download(... allow_patterns="*_asr/*.parquet")` — ASR shards only, TTS excluded unless a subsystem needs it.
2. **Empty/null transcription audit.** Count and log per-language empty/null `transcription` rates; filter (`.filter(lambda x: len(x["transcription"]) > 0)`) before pinning. Don't assume presence — verify.
3. **Transcription-quality QA pass.** Re-transcribe a sample (or full set, budget permitting) with a second ASR pass; compute edit distance per clip; flag/exclude high-divergence or corrupted rows. Replicates the `galsenai/WaxalNLP` community fork's technique for catching misaligned transcriptions.
4. **Checksum and freeze.** Checksum the filtered corpus; commit as the Phase 0 harness artifact. Record the HF revision/commit hash, language codes, and per-language pre/post-filter row counts in the harness README — the provenance record that makes a Context Score defensible.

## Related

- [AfroBench](afrobench.md) — the textual half of Linguistic Fidelity
- [WAXAL-NET subsystem](../subsystems/waxal-net.md) — the edge fine-tuning loop built on this substrate
- [Context Score](../concepts/context-score.md) — Linguistic Fidelity vector
- [Phases — Phase 0](../build-plan/phases.md) — harness freeze gate
- [Synthesis](../synthesis.md) — language/hour count discrepancies to pin
