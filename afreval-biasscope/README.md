# afreval-biasscope

§3.3 adversarial probe discovery loop. Discovers LLM-as-judge bias across
languages before it penetrates production — the **Cultural Safety** vector's
guard against the 43%-acceptance-gap failure mode
([LLM-as-Judge Bias](../wiki/concepts/llm-as-judge-bias.md)).

## Loop contract (§3.3)

| Field | Value |
|---|---|
| Frozen harness | LLM-judge harness + low-resource-language corpus (pinned reference suite) |
| Mutable artifact | `probes/perturbation_program.py` — the perturbation-generation strategy |
| Instruction file | `program.md` |
| Metric | **acceptance-rate delta across languages** under a fixed decision threshold (plus pairwise accuracy for contrast) |
| Budget | fixed **number of judge API calls** per round (cost-bound, not time-bound) |
| Loop flavor | `git commit`/revert style, cost-budgeted |
| Language | Python |

## How it works

1. Seed probe items from the pinned reference suite (semantically identical
   content rendered in eng/fra/swh/yor/hau/ibo/amh).
2. The agent's perturbation program generates stylistic variants (code-switch,
   register, cultural idiom).
3. A judge backend scores each rendering (0–100 + accept/reject at the fixed
   threshold).
4. `run_probe.py` reports the acceptance-rate gap across languages + per-language
   mean scores. A large gap under high pairwise accuracy = the §3.3 phenomenon.

## Backends

- `mock` — deterministic (simulates uncertainty-driven generosity toward
  low-resource languages) for tests + pipeline verification.
- `omlx` — the local MLX server (OpenAI-compatible, port 8787) as a real judge.
- `api` — placeholder for a hosted judge (needs key).

## Live run — 2026-08-05 (Qwen3.6-35B-A3B via omlx)

First real-judge BiasScope run. Fixed two harness defects en route: (1) the
`--max-calls` budget left unscored languages with empty score lists →
ZeroDivisionError; (2) the judge model emits a thinking preamble, breaking
float parsing (all scores silently fell back to 50.0) — fixed by passing
`chat_template_kwargs: {enable_thinking: false}`.

Results (`results/run_omlx_*.json`, 14 judge calls per style): the real judge
shows a **genuine cross-language acceptance gap** — e.g. `code_switch` accepts
eng (97.5) and hau (87.5) while rejecting ibo (17.5) and swh (20.0); delta 1.0.
`high_perplexity` accepts swh (90.0) but rejects fra (0.0). The bias is real and
direction varies by style — not the mock's simple "low-resource = generous"
shape. This feeds the Cultural Safety corrective weighting.

## Run

```bash
# deterministic demo (mock judge)
afreval-harness/.venv/bin/python run_probe.py --backend mock
# real judge via local omlx (start: omlx serve --model-dir ~/.omlx/models)
afreval-harness/.venv/bin/python run_probe.py --backend omlx --style code_switch --max-calls 40
```

## Related

- [BiasScope subsystem](../wiki/subsystems/biasscope.md)
- [Context Score — Cultural Safety](../wiki/concepts/context-score.md)
- [Risk register — judge-API budget](../wiki/build-plan/risk-register.md)
