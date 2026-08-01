# §3.1 tokenizer search — agent operating instructions

Your job: minimize the mean fertility premium vs English across the pinned
language table WITHOUT regressing English CPT by more than 5%. N'Ko and
Ethiopic premiums are scored independently — a win on Latin does not offset a
regression on either.

## Setup (one-time)

1. Read `README.md`, `../afreval-harness/harness/tokenizer_eval.py`, and
   `candidates/tokenizer_candidate.py`.
2. Ensure the afri-fertility venv exists and works:
   `afreval-harness/.venv/bin/python -c "import afri_fertility"`.
3. Create the baseline: `afreval-harness/.venv/bin/python run_experiment.py --baseline`
   (records o200k_base script premiums + English CPT into `baseline.json`).
4. Initialize `results.tsv` with the header row if missing.

## The loop

1. Read the current state: the candidate in `candidates/tokenizer_candidate.py`
   (via `ACTIVE_CANDIDATE`) and `results.tsv`.
2. Pick ONE focused change to the candidate (vocab construction, pre-tokenizer,
   merge order, vocab size, byte-fallback threshold). Make ONE change.
3. `git commit` your change (before evaluating) on an `autoresearch/<tag>` branch.
4. Evaluate: `afreval-harness/.venv/bin/python run_experiment.py`
5. Read the verdict from the log/`results.tsv`:
   - `PASS` — all script premiums ≤ baseline AND English CPT regression ≤5%.
   - `FAIL_CPT_REGRESSION` — English CPT dropped more than 5%.
   - `FAIL_SCRIPT_REGRESSION` — N'Ko or Ethiopic premium rose above baseline.
6. If `PASS`, advance the branch. If `FAIL`, `git revert` and try the next idea.
7. Append the result row to `results.tsv` (tab-separated):
   `commit  candidate_id  latin_premium  ethiopic_premium  nko_premium  english_cpt  status  note`

## Rules

- **Only edit `candidates/tokenizer_candidate.py`.** The harness, the runner,
  and `baseline.json` are frozen.
- No new dependencies beyond what `afreval-harness` already provides.
- All else equal, simpler is better.
- The goal is the lowest script-stratified premiums that keep English CPT —
  NOT a degenerate tokenizer (no returning the raw text, no per-language
  hardcoding unless justified).
- Keep going autonomously until stopped; log every experiment.
