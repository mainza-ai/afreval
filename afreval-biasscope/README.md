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

## Run

```bash
# deterministic demo (mock judge)
afreval-harness/.venv/bin/python run_probe.py --backend mock
# real judge via local omlx (start: omlx start)
afreval-harness/.venv/bin/python run_probe.py --backend omlx --max-calls 40
```

## Related

- [BiasScope subsystem](../wiki/subsystems/biasscope.md)
- [Context Score — Cultural Safety](../wiki/concepts/context-score.md)
- [Risk register — judge-API budget](../wiki/build-plan/risk-register.md)
