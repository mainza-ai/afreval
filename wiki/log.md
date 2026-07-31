---
type: overview
tags: [log, timeline]
updated: 2026-07-31
---

# Wiki Log

Append-only chronological record of wiki activity. Parseable with `grep "^## \[" log.md | tail -5`.

## [2026-07-31] bootstrap | Initial wiki creation

Created the Milimo AfrEval wiki from the two source documents in `dev-docs/` plus the three substrate repos. Wrote schema, home, index, synthesis, 6 concept pages, 3 substrate pages, 6 subsystem pages, 3 infrastructure pages, 2 strategy pages, 3 build-plan pages, and 2 source pages. Logged flagged discrepancies between sources in `synthesis.md`.

## [2026-07-31] ingest | Milimo_AfrEval_Implementation_Bible.md

Ingested the **Implementation Bible** (v1.0 build spec). Established the Karpathy Loop as the core design pattern, the six-subsystem architecture (§3), infrastructure & trust boundary (§4), phased build plan (§5), and risk register (§6). Wrote source page `sources/implementation-bible.md` and propagated its specifications into all concept, substrate, and subsystem pages.

## [2026-07-31] ingest | Milimo AfrEval Implementation Research.md

Ingested the **Implementation Research** blueprint. Established the epistemological crisis framing (African Language Tax, evaluation bias), the Context Score methodology, zero-trust infrastructure strategy, and the regulatory/SaaS business layer. Wrote source page `sources/implementation-research.md` and propagated its framing into concept and strategy pages.

## [2026-07-31] repo | Initialize & push to GitHub

Initialized the workspace as a git repo (`main`), added origin `https://github.com/mainza-ai/afreval.git`, and pushed the wiki + dev-docs + substrate clones (commit `0d6c6c2`). Initial structure registered `autoresearch`/`AfroBench`/`afri-fertility` as git submodules.

## [2026-07-31] repo | Flatten substrate repos

Per the decision to re-engineer the substrate repos in-place, replaced the three submodules with vendored, flattened content so `train.py`/`prepare.py`/`program.md` edits live in-repo (commit `024346a`). Local git history dropped; repos remain re-clonable from upstream.

## [2026-07-31] repo | Restore lm-evaluation-harness as submodule

`AfroBench/lm-evaluation-harness` (~16k files) converted back to a git submodule of EleutherAI/lm-evaluation-harness, pinned to upstream HEAD `f4d4b3de` — verified byte-identical to the previously flattened tree (commit `4beb0db4`).

## [2026-07-31] docs | README + wiki repo-status update

Created top-level `README.md` (structure, clone/sync commands, three-layer pattern). Updated wiki: substrate location lines, karpathy-loop vendored note, AGENTS.md raw-source layer, home.md repository-status section, repository-layout current-vs-target note, and this log.

## [2026-07-31] report | Tauri integration investigation

Researched Tauri v2 (Rust backend, webview frontend, mobile support, capability/CSP security model, sidecars). Wrote `reports/tauri-integration.md` for human review: recommends adopting Tauri for an air-gapped `afreval-onprem` certification + security-dashboard client in Phase 5, embedding the Rust scorer/validator as crates and reusing the dashboard frontend; explicitly not for the Flutter field app or the server-side zero-trust runtime. Added `reports/` to schema and index.

## [2026-07-31] decision | Adopt Tauri 2 (afreval-onprem)

Human approved Tauri integration. Decisions recorded in report §10: (1) air-gapped client is strategically core, built Phase 5, de-risked from Phase 1–2 via clean crate boundaries + frontend build-target-agnostic; (2) security dashboard included in same on-prem release, cert-first; (3) local MCP server post-MVP, all tool execution airlock-gated from day one; (4) Linux targets Ubuntu LTS (.deb+AppImage) + Debian secondary, no RPM v1, WebKitGTK declared/tested. Added `afreval-onprem` to the target repository layout (now 11 repos).

## [2026-07-31] impl | Phase 0 harness freeze (afreval-harness v0.1.0)

Implemented `afreval-harness/` in-tree per the Phase 0 gate. Pins: `afri_fertility.yaml` (frozen, 5 artifacts checksummed) and `afrobench_lite.yaml` (frozen, 9 artifacts checksummed — 7 tasks, 14 languages, validated against the vendored lm-eval group); `waxal.yaml` left **pending-freeze** — §2.1.1 acquisition+QA is the Phase 0 blocker. Built `harness/tokenizer_eval.py` (§3.1 script-stratified eval — reproduced afri-fertility reference numbers exactly, e.g. Yoruba 2.464×, Amharic 7.834×), `harness/waxal_eval.py` (pure deterministic WER/CER), `harness/afrobench_eval.py` (vendored-drift detection), `harness/pins.py`, acquisition/freeze/bump scripts, PROVENANCE.md, 16 pytest cases passing. Tagged v0.1.0. WAXAL remains the open gate (see [phases.md](build-plan/phases.md)).

## [2026-07-31] impl | WAXAL §2.1.1 corrected to Hub ground truth

Verified `google/WaxalNLP` on the Hub (repo sha `e0a62aa`): per-language/per-task configs; each `{lang}_asr` config ships labeled `train`/`validation`/`test` splits (every row carries `transcription`) plus a large `unlabeled` split (`transcription == ""`). Transcribed-vs-untranscribed is separated **by split**, not by a filter inside the labeled data — the paper's "~10% transcribed" describes pre-release collection. **19 ASR configs published** (matches the WAXAL-NET set; resolves the 21–27 vs 24 language discrepancy in synthesis.md). Updated `scripts/acquire_waxal.py` to pull labeled splits only (never `*-unlabeled-*`), verify empties (filter only >0.1%), and treat the second-ASR edit-distance + audio-integrity pass as the real filter. Updated `pins/waxal.yaml`, harness README, and [waxal.md](substrates/waxal.md). Dry-run resolves all 19 configs; 16 tests passing.

## [2026-07-31] impl | WAXAL two-stage acquisition (eval-first)

Full ~1,250h pull (~52 days at observed Hub transfer rates) buys nothing for Phase 0 — the harness only scores the held-out eval split. Decided and implemented **two-stage, eval-first**: Stage A (now) acquires `validation`+`test` only (~2% of the collection, ~1–2 days), the frozen WER/CER harness; Stage B (Phase 4) pulls labeled `train` on-demand for WAXAL-NET fine-tuning; `unlabeled` is never acquired (pretraining-only). `acquire_waxal.py` defaults to `--splits validation test`, materializes audio (decode failures raise — never enter the harness) into `data/waxal/audio/`, writes per-config JSONL manifests + transcription audit. Added `soundfile` to the `[waxal]` extra (audio decoder). Pin + runbook + [waxal.md](substrates/waxal.md) updated.

## [2026-07-31] impl | WAXAL loader caveat + corrected acquisition

Discovered the background pull was downloading `unlabeled` shards: `datasets.load_dataset()` materializes the WHOLE config (all splits) even when one split is requested. Killed it and rewrote `acquire_waxal.py` to `snapshot_download(allow_patterns="data/ASR/*/*-{split}-*.parquet")` + local pyarrow reads (audio is embedded in the parquet; no separate fetch). Dropped the `datasets` dependency from `[waxal]` (added `pyarrow`).

## [2026-07-31] impl | WAXAL Stage A acquisition complete

Ran the corrected Stage A pull end-to-end: **all 19 `_asr` configs, `validation`+`test`, 76,107 rows, 0 empty transcriptions**, ~21GB audio materialized in `data/waxal/audio/` (decode-verified per clip), 0 unlabeled / 0 train downloaded. Manifests + audit committed; heavy artifacts gitignored (re-pullable from pinned revision `e0a62aa`). Phase 0 remaining: second-ASR QA pass, then `freeze_checksums.py --pin waxal.yaml` closes the gate.

## [2026-07-31] qa | WAXAL corpus-level audio anomaly — QA-BLOCKED

The second-ASR QA pass exposed a corpus-wide problem instead of validating the data: **Whisper (large-v3-turbo, both ctranslate2 and MLX implementations) fully degenerates on WAXAL clips** (infinite repeated-character loops) while transcribing known-good English TTS perfectly. Diagnosed via: (1) audio integrity — valid 128kbps mp3s, soundfile/ffmpeg decoders agree exactly, real voiced-band energy; (2) local **Qwen3.6-35B VLM** spectrogram analysis (via the user's `omlx` server, port 8787) — clips show **discrete periodic broadband pulses in clean −80dB silence, no formant structure**, vs normal speech for the EN control; (3) quantitative scan of 150 clips across all 19 languages — **median silence 33–68%**, 75% of clips >35% silence, 95% pulse-dominated (normal speech ~4–10%).

Conclusion: the eval-split audio does not match its long image-description transcriptions — same failure class the galsenai/WaxalNLP fork reported (misaligned audio). **WAXAL is QA-BLOCKED; the harness must not be frozen on trust.** Next steps: human/linguist listening check on a stratified sample + corpus-source investigation (paper methodology, alternate mirrors). Note: this is exactly what §2.1.1 step 3 exists to catch — the "don't assume, verify" discipline just earned its keep.

## [2026-07-31] qa | WAXAL anomaly confirmed — not a Whisper issue

Per user direction, investigated newer-model hypotheses from altic-dev/FluidVoice and huggingface/speech-to-speech (both default to NVIDIA Parakeet TDT v3 / Nemotron Speech 3.5 — modern but cover only ~25-40 mostly-European languages, not the 19 WAXAL set). Ran the decisive second opinion with **Meta MMS** (facebook/mms-1b-all, CTC-based, 1,100+ languages incl. Amharic, cannot produce loop-degeneration): it outputs **random character garbage (WER 1.0) on the same amh clip while transcribing the English control perfectly**. Three independent ASR families (Whisper-ctranslate2, Whisper-MLX, MMS-CTC) now fail identically on WAXAL audio while all handle clean speech. **Conclusion: the corpus audio genuinely lacks the transcribed speech — a data issue, not a model version issue.** QA-BLOCKED stands; next step is corpus-source investigation / human listening.
