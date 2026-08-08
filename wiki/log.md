---
type: overview
tags: [log, timeline]
updated: 2026-08-05
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

## [2026-07-31] qa | CORRECTION — WAXAL corpus is VALID (false alarm)

The QA-BLOCKED finding was **wrong**. Per user's pointer, tested African-language ASRs: `badrex/Ethio-ASR-multilingual-600M` (wav2vec2-bert-2.0 **fine-tuned on google/WaxalNLP**, CTC — cannot loop-degenerate) transcribes the exact clips Whisper/MMS failed on at **normal WER** (amh 0.18, tir 0.38, orm 0.41, sid 0.27, wal 0.46 across validation clips — consistent with the model card's WAXAL test-set WERs). The corpus contains the transcribed speech. **Why general ASRs failed:** WAXAL is spontaneous, natural-environment speech — zero-shot foundation ASRs trained on clean studio audio fail on it, which **empirically reproduces the WAXAL-NET thesis** (tuned models beat zero-shot on spontaneous African speech). QA-BLOCKED lifted; pin status back to acquired-awaiting-QA. Correct QA methodology: second pass with WAXAL-tuned ASRs — Ethio-ASR for amh/tir/orm/sid/wal (open) and `Sunbird/asr-whisper-51-african-languages` for the other 14 (gated — requires HF login/token). Lesson logged: use corpus-appropriate ASRs for QA, and treat "general model fails" as a model property, not necessarily a data defect.

## [2026-07-31] qa | Full QA pass 2 launched (WAXAL-tuned ASRs)

Verified Sunbird (`Sunbird/asr-whisper-51-african-languages`, HF token authed as Maiking) after user accepted the gated conditions — transcribes ach (WER 0.16–0.35), sna (0.04–0.28), amh (0.44–0.69) correctly. Wrote `scripts/qa_waxal_tuned.py` (per-config routing: Ethio-ASR → amh/tir/orm/sid/wal, Sunbird → ach/aka/dag/dga/ewe/ful/kpo/lin/lug/mlg/nyn/sna/sog(xog); resumable; adaptive per-language outlier thresholds) and launched **two parallel background passes** (8 threads each): Ethio-ASR (~34.8k clips) and Sunbird (~40.6k clips). `mas_asr` has no coverage in either model — deferred for human QA. Throughput ~24 (Ethio) / ~12 (Sunbird) clips/min on the M3 Max CPU; multi-day background job, fully resumable. Per-clip QA outputs gitignored; `qa2_summary.json` will be committed at completion.

## [2026-07-31] qa | QA pass 2 optimized for M3 Max (MPS + batching)

User pushed for faster processing — right call, CPU per-clip inference was underutilizing the M3 Max. Benchmark on the 16-core/128GB machine: **MPS (unified GPU) + true batching** is the win. `qa_waxal_tuned.py` upgraded: `--device mps`, batched CTC (Ethio-ASR, padding+attention_mask) and batched Whisper generate (Sunbird, attention_mask verified byte-identical to single-clip). Throughput: Ethio-ASR **~173 clips/min** (CPU 24), Sunbird **~50 clips/min** (CPU 12). Critical finding: two MPS processes contend badly (Sunbird fell to 14/min), so the passes now run **sequentially via a shell chain** (Ethio ~3.4h → Sunbird ~13.5h ≈ **17h total**, down from ~80h). Both resumable.

## [2026-07-31] qa | QA paused for reboot (memory pressure), resumed

System hit 95% RAM (peak 126G used / 40G compressor / 5.9G swap) during QA. Diagnosed: not a leak or single process — QA is ~3GB; the bulk was GPU/Metal wired memory + compressed file cache. Stopped `omlx` (35B model), stopped the QA (freed 96GB → 30G used), user rebooted, QA resumed from state (sid 4832→). Copied the QA torch venv to a persistent `afreval-harness/.venv-torch` (survives reboot; /tmp/mmsenv was wiped). Lesson: on this 128GB machine, run heavy GPU workloads serially and watch `vm.swapusage` as the real safety metric.

## [2026-07-31] impl | Phase 1 — deterministic Context Score scorer (afreval-context-score)

Built the Rust scorer (§3.2 non-search half) in-tree: `src/report.rs` (model evaluation report + validation), `src/config.rs` (per-vertical weights YAML, Σweights=1 enforced), `src/score.rs` (deterministic pipeline — only +−·/min/max, no transcendentals), `src/main.rs` (CLI: `score`/`validate`). Weights: `telco.yaml`, `banking.yaml` (per-industry, the mutable artifact). 6 tests pass incl. **bit-identical repeated-run determinism** (Phase 1 acceptance). CLI verified end-to-end (example model: telco 63.27/fail, banking 67.91/fail; two runs byte-identical via `cmp`). `research/` placeholder documents the Phase 3 calibration loop (fitness-function-first). Also flagged the era-bound AfroBench findings (GPT-4o/Gemini 1.5 Pro are 2024–25; re-benchmark current frontier models at certification time).

## [2026-07-31] impl | Phase 1 — §3.1 tokenizer search loop + harness→scorer bridge

`afreval-tokenizer-research/`: training-style §3.1 loop — `candidates/tokenizer_candidate.py` (mutable artifact: byte-fallback + char candidates), `run_experiment.py` (deterministic scoring vs baseline, enforces English CPT regression ≤5% + independent N'Ko/Ethiopic), `program.md` (agent instructions), `results.tsv`. Verified: baseline o200k_base english_cpt 5.73 / latin 1.55 / ethiopic 7.83; both naive candidates correctly rejected (FAIL_CPT_REGRESSION). `afreval-harness/harness/report.py`: ModelReport builder bridging harnesses→scorer; end-to-end demo scored a real report (o200k_base premium 2.68 → Context Score 57.77, below telco 70 → fail — the Language Tax in action).

## [2026-07-31] impl | Phase 2 — afreval-airlock validator (four seams + JWS clearance)

Rust tool-call validator (§3.5) in-tree: seam 1 deny-by-default allowlist, seam 2 ghost-arg stripping + schema/type validation, seam 3 output cap + PII masking, seam 4 per-call reauthorization via JWS HS256 clearance pinned to the operator trust-root key (with expiry + tool-binding). CLI (`grant`/`validate`) verified end-to-end: `rm_rf` denied on allowlist, ghost args stripped, valid grant → Allow, tampered/expired/wrong-tool grants → RequireReauth. **12 per-seam regression tests passing.** README documents the §3.5 hardening loop (confirmed bypass → permanent regression test) and the vendor-vs-reimplement note (seam 4 is the genuinely-unbuilt piece; seams 1–3 exist upstream in sattyamjjain/agent-airlock).

## [2026-08-01] impl | §3.5 hardening loop + trained BPE candidate + afreval-onprem skeleton

- **afreval-airlock hardening loop**: `attack/attack_program.js` (mutable red-team payload catalogue, 20 variants/4 seams), `attack/run_attack.js` (runner → batch validator → **per-seam bypass rate**; seam-aware neutralization semantics; exit 1 on bypass), `attack/program.md`. CLI gained `--batch` validate + `sanitize`. Result: **0 bypasses**; loop caught a real artifact (JS `{__proto__:…}` literal sets the prototype — key never serialized; fixed via JSON.parse).
- **afreval-tokenizer-research trained BPE**: `candidates/bpe_trainer.py` (script-agnostic BPE), `train_bpe.py` (reference suite + WAXAL transcription sample, 61.8k words), `TrainedBPE` candidate. Result: premiums collapse (latin 1.55→0.91, ethiopic 7.83→1.06) but English CPT 5.73→1.80 → **FAIL_CPT_REGRESSION** — correctly enforces the §3.1 Pareto constraint.
- **afreval-onprem Tauri 2 skeleton** (Phase 5 prep): embeds `afreval-context-score` + `afreval-airlock` as crates (cargo check passes); commands `score_report` / `validate_tool_call` / `clearance_status`; static frontend shell; Stronghold vault + dashboard reuse + local MCP server are post-MVP per report §10. Also gitignored Rust `target/` and untracked 767 committed build-artifact files.

## [2026-08-01] impl | §3.2.1 certification pipeline + script-aware PASS + security dashboard

- **Certification pipeline** (`afreval-harness/scripts/certify.py`): verifies frozen pins → runs §3.1 harness → builds ModelReport → Rust-scored → auditable cert with sha256. **Deterministic**: repeated runs produce identical `cert_sha256` (the §3.2.1 reproducibility requirement). This is the certification loop, never agent-optimized.
- **Script-aware candidate PASSES** (§3.1): `ScriptAwareCandidate` = o200k_base for Latin + trained BPE for Ethiopic/N'Ko. **Ethiopic premium 7.83 → 3.38 (−57%) at zero English-CPT regression** — the first candidate to satisfy the §3.1 constraints. The loop caught a real bug en route (Yoruba `ẹ/ọ/ṣ`, Latin Extended Additional U+1E00+, misdetected as Ethiopic by a coarse `>=0x1200` check — fixed with precise Unicode blocks).
- **Security dashboard surface** in `afreval-onprem`: `security_report` command → last hardening-loop report rendered (per-seam bypass rates, never aggregated).
- **Wiki**: phases.md Phase 0/1/2 statuses, repository-layout implemented-repos list.

## [2026-08-01] qa | WAXAL QA pass 2 COMPLETE (74,400 clips)

Sunbird pass finished (sna, sog last). Total: **74,400 clips QA'd across 18 languages** (Ethio-ASR 5 + Sunbird 13; `mas_asr` has no model coverage). `finalize_waxal.py` → **2,255 clips (3%) flagged** for human review (adaptive per-language threshold or WER≥1.0 or decode_failed), written to `data/waxal/qa2_review.md` + `qa2_drops.json`. Notable high-rate configs: **kpo 747 (21%)**, lin 337 (9%), tir 267, wal 232, mlg 173. Pin status: **QA-COMPLETE-AWAITING-APPROVAL**. Next: human reviews the drop list → `finalize_waxal.py --apply` → `freeze_checksums.py --pin waxal.yaml` → **Phase 0 closed**.

## [2026-08-01] impl | Phase 0 CLOSED — WAXAL frozen (72,145 clips)

Per the proceed directive: applied the QA drop list (`finalize_waxal.py --apply`) and froze `waxal.yaml`. **QA-approved frozen corpus = 72,145 clips / 18 languages** (`mas_asr` excluded — no ASR-model coverage). Fixed two freeze bugs en route: (1) configs with zero flagged rows weren't getting a filtered manifest (their rows vanished from the frozen corpus — e.g. Luganda's 1,302); (2) `freeze_checksums` globbed the original manifests instead of the QA-approved filtered ones. All three pins now **frozen**; PROVENANCE.md records the freeze. **Phase 0 complete — Phase 4 (WAXAL-NET) unblocks.**

## [2026-08-01] impl | Final repos — afreval-sdk + afreval-field-app (all 11 in-tree)

- **afreval-sdk**: Python client SDK (`AfrevalClient.certify`) wrapping the deterministic Rust scorer — auditable certs with sha256, 2 tests passing; TypeScript client shape for the future SaaS API.
- **afreval-field-app**: Flutter scaffold — image-prompted elicitation UI + on-device eval telemetry (local WER, queued sync); spec scaffold, needs the Flutter SDK (not installed). Builds in parallel with WAXAL-NET per §3.4.
- **All 11 target repos now have in-tree presence.** Remaining is operational: Stage B train pull (background), live BiasScope run via omlx, compliance citation sourcing (AU/Malabo), and the server-side isolation tiers (gVisor/Firecracker/Envoy — laptop-unbuildable).

## [2026-08-01] impl | §3.3 BiasScope probe loop + §3.6 compliance loop + afreval-dashboard + onprem vault

- **afreval-biasscope** (§3.3): `probes/perturbation_program.py` (mutable; seeds from the pinned reference suite's parallel translations), `judge/backends.py` (frozen harness: mock deterministic / omlx real / api placeholder), `run_probe.py` (reports the §3.3 metric — acceptance-rate delta across languages under a fixed threshold), `program.md` (cost-bounded instructions). Mock demo shows the blind spot deterministically (English rejected, low-resource generously accepted → 1.0 delta); 4 tests.
- **afreval-compliance** (§3.6): `citations/africa.yaml` (mutable mapping), `check_currency.py` (citation resolves + key phrase at authoritative source; --offline), `program.md`. Kenya ODPC + Nigeria NDPC **current**; AU AI Strategy + Malabo Convention **unverified** (TBD — must be sourced from official AU pages; a failure state, not a placeholder); 3 offline tests.
- **afreval-dashboard**: Phase 5 certification & security web surface (certs + per-seam bypass rates from state.json; the build-target-agnostic UI the onprem client mounts).
- **afreval-onprem**: seam-4 trust-root `Vault` stub ($AFREVAL_TRUST_KEY; Stronghold post-MVP) + `sign_grant` command.

All 11 target repos now have in-tree presence (see the entry above).

## [2026-08-03] impl | acquire_waxal Stage B: train pull allowed on frozen pin

`acquire_waxal.py` frozen-pin guard previously blocked *all* re-acquisition; relaxed to block only the eval split (`validation`/`test`). `--splits train` now proceeds as the Stage B fine-tuning substrate, separate from the frozen eval harness. Stage B train pull launched in background (commit `ce1e435e`).

## [2026-08-03] impl | Compliance 100% citation currency + real frozen-data certification

- **afreval-compliance**: AU Continental AI Strategy → au.int official document page (`20240809/continental-artificial-intelligence-strategy`); Malabo Convention → au.int official treaties page. `check_currency.py` now reports **4/4 current** (AU + Malabo + Kenya ODPC + Nigeria NDPC) — the AU/Malabo failure state from the §3.6 entry above is closed.
- **Real certification** on frozen-harness data: `certs/zero-shot-baseline.cert.json` — zero-shot baseline Context Score **53.88** (below telco 70 → **fail**, cert sha256 `f52acbb8`). The Language Tax in action on a real certified report.

## [2026-08-03] impl | Stage B blocked on upstream HF Xet 404s (recorded in pin)

Train-split download hit **HF Xet storage 404s** at pinned revision `e0a62aa` (resolve + CAS reconstruction both fail for train blobs; Stage A val/test pulled fine). Retry loop killed; resumable from cached shards when HF recovers. **Stage B is a Phase 4 substrate, not a Phase 0 blocker** (Phase 0 frozen). Recorded in `pins/waxal.yaml` + `data/waxal/stageb.log` (commit `cea785ca`).

## [2026-08-05] audit | Cross-repo gap analysis + implementation plan
Audited all 11 repos against the Bible + phases. Wrote `build-plan/gap-analysis.md`: 16 cross-cutting/subsystem gaps (G1–G5, H1–H3, C1–C2, T1–T2, A1–A3, B1–B4, L1–L2, W1–W2, F1, D1, S1–S2, O1–O2), 3 spec-vs-implementation gaps (code-mixing metrics, OOD protocol, threshold calibration), each tagged **UNBLOCKED** (actionable now) or **BLOCKED** (external dep). Prioritized implementation plan in 5 phases: A integrity/automation (CI, auto cert inputs, SDK packaging), B correctness/coverage (N'Ko scoring, airlock replay protection, BiasScope config/mock fidelity, compliance registry, trust-root hygiene), C the certification API layer (unblocks the whole SaaS surface), D data-gated (Stage B → MLX fine-tune, calibration loop, field-app), E server-class hardening (gVisor/Firecracker/Envoy, Stronghold). Highest-value unblocked items: **A1 CI**, **A2 automated certification inputs**, **B2 airlock replay protection**.

## [2026-08-05] impl | §3.3→§3.2.1 bias-correction bridge wired into certification

The certification pipeline consumed a "BiasScope-corrected judge score" but nothing computed it. Added `afreval-biasscope/bias_correct.py`: converts the **worst-case acceptance-rate delta** across live probe runs into the correction — `corrected = raw × (1 − min(delta,1) × 0.5)` (conservative default; tunable per-vertical by the §3.2 calibration loop). Wired into `certify.py --bias-correct-from <results dir>`, with the correction provenance embedded in the cert.

Full end-to-end cert (2026-08-05): zero-shot-baseline, SIB-200 tokenizer + BiasScope correction (delta 1.0 → raw judge 70 → 35) → **Context Score 54.55** (was 61.55 without correction, 53.88 with baseline tokenizer). Cert `certs/zero-shot-baseline-sib200-bc.cert.json` (sha `74f21c5b`), **bit-identical across runs**. This is the first cert that exercises all three closed loops: §3.1 tokenizer → §3.2.1 scorer → §3.3 cultural-safety correction. Dashboard state regenerated (4 certs).

## [2026-08-05] impl | §3.2.1 certification reflects the §3.1 win

`certify.py` gains `--tokenizer-candidate` (loads the §3.1 loop's current best from `afreval-tokenizer-research`). Re-certified the zero-shot-baseline model with the SIB-200 tokenizer — **same model, same WER/accuracy/judge, only the tokenizer changed**:

- Context Score **53.88 → 61.55** (still fail below telco 70, but a +7.7 move)
- structural economics **37.25 → 62.82** — the African Language Tax penalty nearly halved
- cert sha256 `516d0530` (`certs/zero-shot-baseline-sib200.cert.json`), **bit-identical across runs** (determinism preserved)

This closes the loop §3.1→§3.2.1: the tokenizer search's output now directly improves certified Context Scores. Dashboard state.json regenerated (3 certs + latest security report: 31 variants, 0 bypasses).

## [2026-08-05] impl | §3.5 hardening round — 2 bypasses found, both fixed

Expanded the `afreval-airlock` attack catalogue 20 → 31 variants (unicode homoglyphs, fullwidth confusables, nested-ghost smuggling, capitalized/homoglyph params). The loop found **two real bypasses**, both promoted to permanent regression tests and fixed:

1. **Seam 3 — unicode confusable PII**: `alice@corp.ｉｏ` (fullwidth TLD) evaded the ASCII-only email regex → NFKC normalization added before masking (`src/sanitize.rs`).
2. **Seam 2 — duplicate-key smuggling**: `{"customer_id":"c1","customer_id":"DROP TABLE x"}` deserialized last-wins (RFC 8259 undefined behavior), swallowing the injected value with no ghost-arg strip → `StrictArgs` deserializer rejects duplicate keys at parse (`src/ghost_args.rs`, custom `ToolCall` Deserialize).

The dup-key case is a wire-level defense, regression-tested in `tests/redteam.rs::seam2_duplicate_keys_are_rejected` (not transmittable through the JS harness — `JSON.parse` collapses it first). Rebuilt: **31 variants, 0 bypasses, 21 tests passing.**

## [2026-08-05] impl | §3.3 live BiasScope run — real judge, genuine cross-language gap

Ran the BiasScope loop end-to-end against a real judge for the first time: **Qwen3.6-35B-A3B via local omlx** (started `omlx serve --model-dir ~/.omlx/models`, port 8787; machine idle 128GB/no swap). Four real perturbation styles implemented in `probes/perturbation_program.py` (was a placeholder that ignored the style parameter): code_switch, colloquial, formal, high_perplexity. Two harness defects fixed: (1) `--max-calls` budget left unscored languages → ZeroDivisionError; (2) judge's thinking preamble broke float parsing → every score silently fell back to 50.0, fixed via `chat_template_kwargs: {enable_thinking: false}`.

**Result: genuine cross-language acceptance gap**, direction varying by style (not the mock's simple low-resource-generosity shape). code_switch accepts eng 97.5/hau 87.5 but rejects ibo 17.5/swh 20.0 (delta 1.0); high_perplexity accepts swh 90.0 but rejects fra 0.0; formal accepts yor 87.5 but rejects ibo 2.5. Results in `results/run_omlx_*.json`. Feeds the Cultural Safety corrective weighting. 4 tests passing.

## [2026-08-05] impl | §3.1 Latin-African gap closed — SIB-200 corpus mix

The documented §3.1 open problem was that Latin premiums stayed at baseline because the BPE training corpus had no Yoruba/Hausa/Igbo/Swahili (WAXAL TTS-only). Per §2.3 the pinned SIB-200 corpus is the source for that gap; verified **FLORES is gated, SIB-200 is open** (Davlan/sib200). Extended `train_bpe.py` with `--sib200-per-lang <n>` (6 African-Latin languages, train+test, 5,430 sentences). Trained BPE at 500/2000/2500/5000/8000 merges; the 8,000-merge candidate with `EfficientRouteCandidate` routing gives:

- **latin premium 1.5456 → 1.2876 (−16.7%)**
- **ethiopic premium 3.377 → 2.8255 (−16.3%)**
- **english_cpt exactly at baseline 5.7349 (PASS held)**

All five African-Latin reference-suite languages now route to the BPE (yor 0.63×, ibo 0.82×, hau 0.85×, swh 0.93×); eng/fra stay on o200k via min() routing. Logged in `results.tsv` (`candidate/bpe-sib200-v0..v4`). This is the first candidate to improve Latin AND Ethiopic simultaneously. Stage B (WAXAL train) remains blocked upstream — fine-tuning unaffected by this loop.

## [2026-08-05] impl | Gap-analysis Phase A+B implemented (CI, replay protection, trust-root, auto-inputs, SDK packaging, N'Ko)
Executed the top unblocked items from `build-plan/gap-analysis.md`:

- **A1 — GitHub Actions CI** (`.github/workflows/ci.yml`): harness (20) + biasscope (11) + SDK (2) pytest, airlock cargo tests (25), §3.5 hardening loop (fail on any bypass), certification determinism check (bit-identical sha), TypeScript build+test, Python wheel build. All steps verified locally.
- **B2 — airlock seam-4 replay protection**: grants now carry a `jti` nonce; `ReplayGuard` rejects a grant used twice (fail closed, jti-less grants rejected under guard); optional `grant_call_binding` policy binds a grant to the exact call via canonical hash (`sign_for_call`/`canonical_call_hash`). 4 new regression tests (25 airlock total). 31 attack variants still 0 bypasses.
- **B5 — on-prem trust-root hygiene**: `Vault::from_env` reads `AFREVAL_TRUST_KEY_FILE` then `AFREVAL_TRUST_KEY`; the dev-fallback key is **debug-only** — release builds fail closed (exit 2) with no configured key.
- **A2 — automated certification inputs**: `certify.py --auto-inputs` pulls WER from the frozen QA baseline (`eval_baseline.py`, n=18) and the judge from §3.3 bias correction; provenance recorded in the cert's `input_sources`.
- **A3 — SDK packaging**: TypeScript gains `tsconfig.json` + build + node:test suite (injectable fetch) + wheel; Python wheel builds.
- **B1 — N'Ko third number measured**: added SIB-200 `nqo_Nkoo` to the training mix + `score_nko.py` supplementary scorer. **N'Ko premium 1.5317** (vs ~9× documented worst case). Tradeoff: Latin 1.2876→1.3264 and Ethiopic 2.8255→2.8482 (N'Ko merges crowded the budget), both still below baseline → PASS held.

## [2026-08-05] impl | Gap-analysis B3/B4/B6 + Phase C API + code-mixing + OOD

Second implementation pass over the unblocked gaps:

- **B3 — BiasScope config + mock fidelity**: `config.yaml` (threshold/budget/styles/mock-direction) now exists (program.md referenced it but it was missing); `MockJudge` gains a `strictness` direction (low-resource scored lower — the live-observed opposite of generosity); `ApiJudge` is a real OpenAI-compatible hosted backend (`AFREVAL_JUDGE_URL`/`KEY`). run_probe defaults now read config. 14 biascope tests.
- **B4 — compliance registry expansion**: 4 → **7 citations**, adding AfCFTA (binding) + ECOWAS/SADC (non-binding); every instrument now carries a `binding`/`non-binding` flag surfaced by `check_currency.py` so a strategy is never presented as law. **7/7 current** online.
- **B6 — §3.4 hardware class**: `fine_tune.yaml` gains a numeric `hardware_class` spec (device, ≤4GB RAM, ≤350MB model, RTF≤1.0) + `assert_hardware.py` device-layer assertion (fails loud on mismatch / `--on-gpu`).
- **C1 — certification HTTP API** (`afreval-api/`): FastAPI `/v1/health`, `/v1/certify` (auto-inputs WER/judge server-side), `/v1/security`, `/v1/compliance`. End-to-end verified (api-e2e cert via auto-inputs + SIB-200 + bias correction → 55.46). 4 API tests.
- **C2 — SDKs point at the API**: Python `AfrevalClient(base_url=...)` adds `certify_api`/`security_report`/`compliance` (network mode) alongside the local-scorer mode; TypeScript adds `certifyApi` + `compliance` matching the `/v1/*` contract. Python SDK 5 tests, TS 3 tests.
- **Code-mixing metrics**: `harness/code_mixing.py` implements **CMI, enhanced CMI (α·switch + β·legacy), I-index, M-index** (the Research-doc formulas the Bible lacked). 6 tests. Closes the synthesis flagged gap.
- **OOD protocol (§3.4)**: `ood_protocol.py` defines and measures OOD generalization — per-language silence-tercile split of the frozen eval split, both numbers reported (in-dist 37.56% vs OOD 37.60% balanced; global split shows 36.4% vs 41.8% but drops languages — protocol finding logged). Acceptance: beat baseline macro-WER AND no OOD regression >5 pts.

**Test totals: 52 Python + 25 Rust + 3 TypeScript, all passing.** Remaining blocked: Stage B (HF Xet 404), §3.2 calibration (labeled-outcome data), field-app (Flutter), server tiers (gVisor/Firecracker/Envoy), Stronghold.

## [2026-08-05] impl | Open-source-first: Ollama judge + Docker-unblocked D3/E1/D1

**Ollama (open-source judge)** — the project is open-source, so the earlier live BiasScope run (proprietary `omlx`) now has a fully open, reproducible replacement:
- Added `OllamaJudge` (native `/api/chat`, `think:false` — qwen3.6's reasoning otherwise empties content on the OpenAI-compatible `/v1` path) + `api`/`ollama` backends in `run_probe.py`. `bias_correct.py` accepts both `omlx` and `ollama` real-judge runs.
- **Live open-source run**: qwen3.6 via Ollama — **acceptance-rate delta 1.0 on all 4 perturbation styles**; the classic §3.3 generosity pattern reproduced (eng rejected 50, all African languages accepted 85–100 on style=none), with direction varying by style. Cert `zero-shot-baseline-ollama.cert.json` (sha `627a59f2`, cultural safety 35.0 after delta-1.0 correction), deterministic.
- Fixed a real bug my A2 change introduced: `certify.py --wer` default became `None`, so a run without `--auto-inputs` emitted `null` WER → scorer parse failure. Restored default 0.38.

**Docker (available on this machine) unblocks 3 items**:
- **D3 — Flutter field-app verified in a container**: `flutter analyze` clean + **all 5 tests pass** (WER semantics + telemetry queue) via `ghcr.io/cirruslabs/flutter:3.32.5`. Note: `flutter:stable` (3.44) has a broken `vector_math`/`star_border` SDK compile in the container — use 3.32.5.
- **E1 — Envoy credential-injection sidecar live** (`afreval-envoy/`): docker-compose Envoy on :10000 injects `X-AfrEval-Synthetic-Cred` + `X-AfrEval-Credential-Hint` into every request before forwarding to the upstream tool service — verified via echo server (the agent never holds the credential, matching §4). Schema notes recorded (header_mutation filter, no `%ENV%` in header values). gVisor/Firecracker remain infeasible in Docker Desktop (no KVM).
- **D1 — Stage-B retry**: `scripts/retry_stageb.py` (polls upstream, resumes the resumable train pull when HF recovers; `--once` for cron/Docker) + `Dockerfile.stageb`. Verified it correctly reports the 404 and exits cleanly.

**Tests: 53 Python (OllamaJudge test added) + 25 Rust + 3 TS.** Still blocked: Stage B data (upstream), §3.2 calibration (data), gVisor/Firecracker (server-class), Stronghold (post-MVP).

## [2026-08-07] impl | Review remediation R1–R5: Context Profile, diff/staleness, reframe

Four independent reviews converged on the same critiques: the scalar Context Score is reductive, "certification" overclaims authority, one-shot certs decay, and the methodology isn't published. Implemented:

- **R1 — Context Profile** (`harness/profile.py`): the cert now carries per-language fertility/premium/CPT (+WER for 18 langs), per-script premiums, `as_of`, `re_cert_after`. Exposed in `/v1/certify` + `/v1/certs`; dashboard renders the profile table. 6 tests.
- **R2 — Diff + staleness**: `/v1/diff?base&target` (per-language/script/vector deltas), `/v1/certs/stale`, `/v1/certs/{sha|model}`; Python + TS SDKs gained `diff`/`list_certs`/`get_cert`/`stale_certs`. 4 API tests, 1 TS test.
- **R3/R5 — Reframe + methodology manifest**: README reworded from "guarantees" → "evidence-linked signal / pre-deployment compliance harness" with a "what it is / isn't" note; certs now carry `methodology` (tokenizer, WER/judge source, bias probe styles, OOD protocol) + `rubric_manifest` (vertical, threshold, weights version, bias weight, judge model, sign-off ref).
- **R6 — live proprietary layer**: deferred pending scope decision (needs a design choice on which corpora to grow).

**Determinism preserved** (bit-identical certs across runs). **63 Python + 25 Rust + 4 TS tests passing.** Rust scorer untouched.

## [2026-08-05] infra | Podman/seccomp isolation tier built + verified in Docker

Implemented `afreval-isolation/` — the open-source, Docker-runnable standard tier (gVisor substitute). `seccomp/deny-network.json`: network syscalls → SCMP_ACT_ERRNO, dangerous syscalls (reboot/ptrace/mount/chroot/setns/…) → SCMP_ACT_KILL, everything else allowed (so the container runtime's own init works). Verified on Docker Desktop (aarch64):
- `--verify`: compute + file IO allowed, network connect **denied** → PASS
- `--verify-kill`: a `reboot(2)` attempt is **terminated** (Bad system call) → PASS

Same profile works under `podman run --security-opt seccomp=…` on a real Linux host. This is the strongest no-KVM boundary (shared kernel + syscall filtering); gVisor/Firecracker remain the server-class target. Docs: isolation-tiers.md, phases.md, gap-analysis E1, README updated.
