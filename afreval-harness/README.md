# afreval-harness — Phase 0 frozen evaluation substrate

The frozen, checksummed harness for Milimo AfrEval. **This package is read-only
to agents** — it is the eval ground truth that every downstream loop scores
against. See the [wiki](../wiki/home.md) for the full project context.

## What is pinned here

| Substrate | Pin | Status |
|---|---|---|
| afri-fertility (§2.3 / §3.1) | `pins/afri_fertility.yaml` — v0.1.0, vendored_commit `8295979d` | **frozen** |
| AfroBench-LITE (§2.2) | `pins/afrobench_lite.yaml` — 7 tasks, 14 languages, lm-eval group `afrobench_lite` | **frozen** |
| WAXAL (§2.1) | `pins/waxal.yaml` — `google/WaxalNLP` ASR configs | **pending-freeze** |

**Phase 0 is not complete for WAXAL until §2.1.1 (steps 1–3) has run end-to-end
and step 4 has been executed.** A raw, un-audited pull does not satisfy the gate.

## Layout

```
pins/*.yaml          # the ONLY place substrate versions are declared
harness/             # read-only scoring code
  tokenizer_eval.py  #   §3.1 script-stratified tokenizer evaluation
  afrobench_eval.py  #   §2.2 LITE pipeline spec + vendored drift validation
  waxal_eval.py      #   WER/CER (pure, deterministic)
  pins.py            #   pin loader/validator + checksum tooling
scripts/             # operational tooling
  acquire_waxal.py   #   §2.1.1 steps 1–3
  freeze_checksums.py#   step 4 / re-freeze
  bump_harness.py    #   human-approved pin bump (never silent)
checksums/           # per-pin sha256 manifests (written at freeze time)
data/waxal/          # acquired, filtered WAXAL ASR corpus (after acquisition)
tests/               # pytest — the harness must stay green
PROVENANCE.md        # append-only pin freeze/bump log
```

## Install

```bash
cd afreval-harness
python3 -m venv .venv && source .venv/bin/activate
pip install -e .          # core (afri-fertility + pyyaml)
pip install -e ".[waxal]" # + datasets/huggingface_hub for acquisition
pip install -e ".[dev]"   # + pytest
```

The harness runtime requires Python ≥3.11. afri-fertility is installed from the
vendored in-tree copy at `../afri-fertility` (pinned, not from PyPI drift).

## Verify the freeze is intact

```bash
pytest
python - <<'EOF'
from harness.pins import load_all_pins
from harness.afrobench_eval import validate_vendored_lite
print(load_all_pins().keys())
print(validate_vendored_lite()["tasks"])
EOF
```

`validate_vendored_lite` cross-checks the pin against the vendored
`afrobench-lite.yaml` and **fails loudly** if the task set drifts — the first
line of defense against silent upstream drift.

## Using the §3.1 tokenizer harness

```python
from harness.tokenizer_eval import TokenizerEval, load_reference_suite

suite = load_reference_suite()   # pinned offline corpus (eng, yor, amh, ...)
eval_ = TokenizerEval()          # refuses to run if the afri_fertility pin isn't frozen
result = eval_.evaluate(adapter, suite)   # adapter: .id + .count(text)->int
result.script_premiums()         # {latin, ethiopic, nko} — three numbers, not one
```

`afreval-tokenizer-research` injects candidate tokenizers by implementing the
same two-method protocol (`.id`, `.count`).

## WAXAL acquisition runbook (§2.1.1)

```bash
# 1. Plan only (no download):
python scripts/acquire_waxal.py --dry-run
# 2. Full acquisition + empty/null audit + filter:
python scripts/acquire_waxal.py --out data/waxal
# 3. QA pass — re-transcribe a sample with a second ASR, compute edit distance
#    against the shipped transcriptions, flag high-divergence rows (see §2.1.1
#    and the galsenai/WaxalNLP technique it replicates).
# 4. Freeze (writes checksums/ + provenance; only valid after 1–3 pass):
python scripts/freeze_checksums.py --pin waxal.yaml
```

## Bumping a pin (the ONLY legitimate way to change versions)

```bash
python scripts/bump_harness.py --pin afrobench_lite.yaml \
  --to <new-version> --reason "<why>" --approved-by "<human>" \
  --vendor-commit <new-hash>
python scripts/freeze_checksums.py --pin afrobench_lite.yaml
```

A bump sets `status: pending-freeze`, clears checksums, and appends to
`PROVENANCE.md`. **Never edit a pin file by hand; never auto-update a harness
dependency.**

## Related

- [Phases — Phase 0](../wiki/build-plan/phases.md) — the gate this repo satisfies
- [Repository layout](../wiki/build-plan/repository-layout.md) — `afreval-harness` in the target layout
- [Risk register — upstream drift](../wiki/build-plan/risk-register.md) — why this discipline exists
