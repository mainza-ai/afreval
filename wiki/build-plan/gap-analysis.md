---
type: report
tags: [gap-analysis, implementation-plan, audit, report]
updated: 2026-08-05
---

# Gap Analysis & Implementation Plan — 2026-08-05

Cross-repo audit of what exists vs. what the [Implementation Bible](../sources/implementation-bible.md) + [phases](phases.md) require. Every gap is tagged **BLOCKED** (external dependency — cannot proceed on this machine today) or **UNBLOCKED** (actionable now).

---

## 1. Cross-cutting infrastructure gaps

| # | Gap | Evidence | Priority |
|---|---|---|---|
| G1 | **No CI/CD** — nothing runs the test suites, the hardening loop, or the determinism check on a schedule or on push | `.github/workflows/` does not exist; all 11 repos' tests are manual | **High** |
| G2 | **No live certification API** — the SDKs' entire surface is hypothetical | Python SDK shells out to a local Rust binary; TypeScript SDK does `fetch("/v1/certify")` against a nonexistent endpoint | **High** |
| G3 | **Hardcoded trust-root dev key** shipped in-tree | `afreval-onprem/src-tauri/src/vault.rs:11` `DEV_KEY`; same key in `afreval-airlock/policies/demo.json` | **High** (security) |
| G4 | **No packaging/distribution** for either SDK | Python `pyproject.toml` unbuilt; TS has `package.json` but **no `tsconfig.json`** and TypeScript isn't installed | Medium |
| G5 | **No orchestration** for continuous loops | Risk register calls for `iii-hq/n-autoresearch`-style orchestration once loops go continuous; nothing exists | Low (premature) |

---

## 2. Subsystem gaps

### afreval-harness
| Gap | Detail | Status |
|---|---|---|
| H1 | **Certification inputs are manual flags** — `certify.py --wer/--accuracy/--judge` are typed in, not pulled from the actual pipelines. A cert is only as trustworthy as hand-supplied numbers. | **UNBLOCKED** — wire `eval_baseline.py --from-qa` (WER) + `afrobench_eval.py` (accuracy) + `bias_correct.py` (judge) into one automated invocation |
| H2 | WAXAL frozen corpus is **18 languages, not 19** (`mas_asr` excluded — no ASR coverage). Paper uses 19. | Documented; needs a model with `mas_asr` coverage or an explicit protocol note |
| H3 | `results.tsv` (tokenizer) has **duplicate rows + empty note columns** | Cosmetic cleanup |

### afreval-context-score
| Gap | Detail | Status |
|---|---|---|
| C1 | **Calibration loop is placeholder-only** — `research/` contains just a README; no weight-search code | **BLOCKED** on labeled-outcome dataset (documented in `research/README.md`) |
| C2 | Per-vertical thresholds (telco 70 / banking 70) are **hand-set, uncalibrated** | **BLOCKED** by C1 |

### afreval-tokenizer-research
| Gap | Detail | Status |
|---|---|---|
| T1 | **N'Ko premium is `nan`** — no N'Ko text in the reference suite, so the third §3.1 number is never actually scored ("three numbers, not one" → effectively two) | **UNBLOCKED** — vendor a small N'Ko corpus into the training/suite path (N'Ko is the worst tax, up to ~9×) |
| T2 | Reference suite is tiny (~200 words/lang); scoring robustness on 5×-10× larger SIB-200/FLORES corpora unproven | Harness is frozen by design — do not mutate; the improvement path is more corpus in the *training* side, not the eval side |

### afreval-airlock
| Gap | Detail | Status |
|---|---|---|
| A1 | **Seam-4 grant has no replay protection** — a valid grant binds only `tool + iat`; any call to that tool within `max_age_secs` passes. No nonce, no request binding | **UNBLOCKED** — add nonce/`jti` + bind grant to the exact call; regression test |
| A2 | `run_attack.js` cannot transmit duplicate-key JSON (JS `JSON.parse` collapses it) — the dup-key defense is only covered by the Rust regression test, not the nightly harness | Harness limitation; documented |
| A3 | `policies/demo.json` is a demo policy with the shared dev key — no per-deployment policy/key management | **UNBLOCKED** for key rotation; policy mgmt belongs with the API layer (G2) |

### afreval-biasscope
| Gap | Detail | Status |
|---|---|---|
| B1 | `program.md` references **`config.yaml` that does not exist** — the budget/threshold config is only CLI args | **UNBLOCKED** |
| B2 | `ApiJudge` is a `NotImplementedError` placeholder | **UNBLOCKED** — hosted-judge backend shape |
| B3 | **Mock judge models only one bias direction** (low-resource generosity); the live run showed direction *varies by style* (formal accepts yor, rejects ibo; code_switch rejects swh). Mock can't represent that | **UNBLOCKED** — add direction-aware mock modes |
| B4 | Bias-correction weight is a fixed **0.5 constant**, uncalibrated | **BLOCKED** by §3.2 calibration (C1) — but the constant's sensitivity should be documented |

### afreval-compliance
| Gap | Detail | Status |
|---|---|---|
| L1 | Coverage is **4 instruments / 4 jurisdictions** — the AU AI Strategy is a *strategy*, not binding law; no granularity below instrument level; no regional (ECOWAS/SADC) or sectoral instruments | **UNBLOCKED** — expand registry; the checker loop is generic |
| L2 | `check_currency.py` only verifies a **key phrase present in HTML** — no legal-text diffing or update tracking | Enhancement |

### afreval-waxal-net
| Gap | Detail | Status |
|---|---|---|
| W1 | `train.py` is a **placeholder** (prints "TODO: wire the MLX fine-tune", returns 1) — no LoRA adapter, no MLX/whisper training, no ONNX/TFLite export, no OOD eval protocol | **BLOCKED** on Stage B train (HF Xet 404) |
| W2 | No numeric **target-hardware-class** definition (risk register says "must be defined before the loop can size its budget") | **UNBLOCKED** — write the definition |

### afreval-field-app
| Gap | Detail | Status |
|---|---|---|
| F1 | Scaffold only; **not buildable** (no Flutter SDK) — recording/telemetry logic unverified | **BLOCKED** (SDK absent) |

### afreval-dashboard
| Gap | Detail | Status |
|---|---|---|
| D1 | Reads a **static `state.json`**; no live refresh, no auth, no per-vertical filter, no calibration view, no incident tracking | **UNBLOCKED** — pairs with G2 (needs the API to be live to go fully real) |

### afreval-sdk
| Gap | Detail | Status |
|---|---|---|
| S1 | Python SDK **computes nothing** — caller passes `bias_corrected_judge_score` + `mean_fertility_premium`; not a network client | **UNBLOCKED** (and blocked-at-scale by G2) |
| S2 | TypeScript SDK: no `tsconfig.json`, TypeScript not installed, never built, dead endpoint | **UNBLOCKED** |

### afreval-onprem
| Gap | Detail | Status |
|---|---|---|
| O1 | **Vault is a dev-fallback** (hardcoded key in `vault.rs`); Stronghold is post-MVP | **UNBLOCKED** (partial) — at minimum: refuse to run in "dev-fallback" without an explicit opt-in; key rotation |
| O2 | `security_report` reads a **file path**; frontend is a thin shell not yet reusing `afreval-dashboard` | **UNBLOCKED** |

---

## 3. Spec-vs-implementation gaps (wiki docs promise more than code delivers)

| Doc promise | Reality | Status |
|---|---|---|
| **Code-mixing metrics** (CMI, I-index, M-index) — [synthesis](synthesis.md) flagged gap | Not implemented anywhere | **UNBLOCKED** — decide scope (harness vs deferred) |
| **OOD generalization as §3.4 secondary metric** | Mentioned in docs/config, no eval protocol | **UNBLOCKED** — protocol doc + hook in `eval_baseline.py` |
| **Context Score threshold** | Per-vertical thresholds exist; *justification* (calibration) doesn't | **BLOCKED** by C1 |

---

## 4. Implementation plan (ordered by ROI and dependency)

### Phase A — Integrity & automation (all UNBLOCKED)
1. **A1. GitHub Actions CI** — on push: run harness (20), airlock (21), biascope (11), SDK tests; run the §3.5 attack runner and fail on bypass; run a determinism check (certify twice, compare sha). This closes G1 and makes every later change reviewable.
2. **A2. Automated certification inputs** — `certify.py` pulls WER from `eval_baseline.py --from-qa`, accuracy from `afrobench_eval.py`, judge from `bias_correct.py`; manual flags become overrides only. Closes H1.
3. **A3. SDK packaging** — add `tsconfig.json` + build + smoke test for TS; `python -m build` + wheel for Python; make Python SDK call the certify pipeline path (not just raw scorer). Closes G4/S1/S2.

### Phase B — Correctness & coverage (all UNBLOCKED)
4. **B1. N'Ko scoring** — vendor a small N'Ko corpus so the third §3.1 number is real. Closes T1. ✅ **DONE 2026-08-05** (premium 1.53 via SIB-200 `nqo_Nkoo` + `score_nko.py`)
5. **B2. Airlock replay protection** — grant nonce + call binding; regression test. Closes A1. ✅ **DONE 2026-08-05** (`jti` + `ReplayGuard` + `grant_call_binding`)
6. **B3. BiasScope config + mock fidelity** — add `config.yaml` (budget/threshold/styles), direction-aware mock modes, `ApiJudge` shape. Closes B1/B2/B3. ✅ **DONE 2026-08-05** (config.yaml, strictness direction, real ApiJudge)
7. **B4. Compliance registry expansion** — add regional/sectoral instruments; document that the AU AI Strategy is non-binding. Closes L1. ✅ **DONE 2026-08-05** (7/7 citations, binding-flagged)
8. **B5. On-prem trust-root hygiene** — fail closed if `AFREVAL_TRUST_KEY` unset in non-dev build; remove shared dev key from the airlock demo policy. Closes G3/O1. ✅ **DONE 2026-08-05** (fail-closed vault)
9. **B6. Hardcode target-hardware-class definition** for §3.4. Closes W2. ✅ **DONE 2026-08-05** (numeric spec + `assert_hardware.py`)

### Phase C — The API layer (UNBLOCKED; unblocks the entire Phase-5 surface)
10. **C1. Minimal certification HTTP API** (FastAPI or Rust `axum`) wrapping `certify.py` + the security report; versioned `/v1/certify`, `/v1/security`, `/v1/compliance`. ✅ **DONE 2026-08-05** (`afreval-api/`, verified end-to-end)
11. **C2. Point both SDKs at it** — Python becomes a real network client; TypeScript is buildable against the live contract. This is the moment the "tollbooth" stops being a metaphor. Closes G2. ✅ **DONE 2026-08-05** (both SDKs in API mode)

Also closed 2026-08-05: **code-mixing metrics** (`harness/code_mixing.py` — CMI/enhanced CMI/I-index/M-index) and the **OOD generalization protocol** (`afreval-waxal-net/ood_protocol.py`).

### Phase D — Data-gated (BLOCKED externally)
12. **D1. Stage B pull** (retry when HF Xet recovers) → **MLX fine-tune loop** → ONNX/TFLite export → OOD protocol. Closes W1.
13. **D2. §3.2 calibration loop** once labeled-outcome data exists; calibrate the 0.5 bias weight (B4) and per-vertical thresholds. Closes C1/C2.
14. **D3. Field-app build** once Flutter SDK present; verify recording/telemetry. Closes F1.

### Phase E — Production hardening (server-class, not laptop-buildable)
15. **E1. gVisor/Firecracker/Envoy isolation tiers.**
16. **E2. Stronghold vault** for seam-4 key material.

---

## Related
- [Phases](phases.md) — what each phase formally requires
- [Risk register](risk-register.md) — the risks this plan mitigates
- [Repository layout](repository-layout.md) — repo ownership
- [Synthesis](synthesis.md) — spec discrepancies this audit surfaced
