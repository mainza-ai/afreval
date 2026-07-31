# afreval-harness — Provenance & Pin Bump Log

Append-only record of every pin freeze and bump. A bump is only legitimate if it
is recorded here with an approver and a reason, and the pin is re-frozen via
`scripts/freeze_checksums.py`. Unrecorded changes invalidate historical Context
Scores (§5 risk register).

## 2026-07-31 freeze | initial harness (v0.1.0)

- `afri_fertility.yaml` — frozen at pinned_version 0.1.0, vendored_commit 8295979d (v0.1.0-2-g8295979).
- `afrobench_lite.yaml` — frozen at vendored_commit 78aaa6e9, lm-evaluation-harness@f4d4b3de (afrobench_lite group, 7 tasks, 14 languages).
- `waxal.yaml` — **pending-freeze**: acquisition + QA (§2.1.1 steps 1–3) must complete before freezing. This is a blocking Phase 0 gate, not an oversight.
- Approved-by: mainza (initial freeze).
