# afreval-compliance

§3.6 compliance & documentation loop. Maintains the mapping between AfrEval's
certification output and each jurisdiction's legal requirements — and keeps the
regulatory citations **current** (a stale citation in a compliance report is a
liability, not a rounding error).

## Loop contract (§3.6)

- **Ground truth:** current law, verified against the actual government source.
- **Mutable artifact:** `citations/africa.yaml` (the mapping).
- **Metric:** automated **citation-currency** — do the citations still resolve
  (and contain their key phrase) when checked against the authoritative source?
- **Loop flavor:** `git commit`/revert style (the `/autoresearch:docs` pattern).
- **Repos:** this one (Python/Markdown).

## The loop

1. `check_currency.py` — verifies every citation in `citations/africa.yaml`
   (HTTP resolve + key-phrase presence). Reports per-citation status + a
   currency score.
2. A stale/unverifiable citation is a failure: the agent updates the mapping to
   current law (sourcing from the authoritative source), `git commit`s, re-checks.
3. Human sign-off before the mapping feeds any certification/compliance output.

## Run

```bash
# online (default)
python check_currency.py
# offline (CI / air-gapped): mark all as unverified, no network
python check_currency.py --offline
```

## Layout

```
citations/africa.yaml   # the jurisdiction mapping (MUTABLE)
check_currency.py       # the currency check (frozen)
program.md              # agent instructions
tests/                  # offline-tested checker logic
```

## Related

- [Compliance loop subsystem](../wiki/subsystems/compliance-loop.md)
- [Regulatory landscape](../wiki/strategy/regulatory-landscape.md)
- [Risk register — stale citations](../wiki/build-plan/risk-register.md)
