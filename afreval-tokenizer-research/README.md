# afreval-tokenizer-research — §3.1 tokenizer & vocab search loop

Python, **training-style** Karpathy Loop (base autoresearch pattern). Kills the
[African Language Tax](../wiki/concepts/african-language-tax.md) at the root by
searching tokenizer candidates over the frozen harness.

## Loop contract (§3.1)

| Field | Value |
|---|---|
| Frozen harness | `afreval-harness/harness/tokenizer_eval.py` (never modified) |
| Mutable artifact | `candidates/tokenizer_candidate.py` (agent edits this file) |
| Instruction file | `program.md` (human-owned, read by the agent) |
| Metric | mean fertility premium, **script-stratified** (latin/ethiopic/nko — three numbers) |
| Budget | fixed wall-clock per candidate build + re-tokenize + score |
| Loop flavor | training-style (modify → eval → keep/discard → log) |
| Language | Python |

## How to run one experiment

```bash
# 1. baseline (one-time): captures o200k_base script premiums + English CPT
afreval-harness/.venv/bin/python run_experiment.py --baseline

# 2. evaluate the active candidate (from candidates/tokenizer_candidate.py)
afreval-harness/.venv/bin/python run_experiment.py
```

The runner logs to `results.tsv` and enforces the §3.1 rules (English CPT
regression ≤5%, no N'Ko/Ethiopic regression vs baseline). The agent keeps or
reverts based on those results — the git commit/revert discipline lives in
`program.md`.

## Layout

```
candidates/tokenizer_candidate.py  # MUTABLE — the agent's artifact
run_experiment.py                  # scores the active candidate (deterministic)
program.md                         # agent operating instructions
results.tsv                        # experiment log (append-only)
baseline.json                      # frozen baseline (generated, do not edit by hand)
```

## Related

- [Tokenizer search subsystem](../wiki/subsystems/tokenizer-search.md)
- [afri-fertility substrate](../wiki/substrates/afri-fertility.md)
- [African Language Tax](../wiki/concepts/african-language-tax.md)
