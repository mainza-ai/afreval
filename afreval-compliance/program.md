# §3.6 compliance loop — agent operating instructions

Maintain `citations/africa.yaml` so every regulatory citation resolves to
**current law at the authoritative government source**. A stale citation in a
compliance report is a liability.

## The loop

1. Run `check_currency.py`. Any `stale`/`unreachable`/`unverified` citation is
   a failure.
2. For each failure: find the authoritative current source (government/regional
   portal), update the URL + key phrase in `citations/africa.yaml`.
3. `git commit` the change, then re-run `check_currency.py` to confirm.
4. Human sign-off before the mapping feeds any certification/compliance output.

## Rules

- Source from the **actual government source**, not a scrape of a scrape.
- `url: TBD` is a failure state, not a placeholder — the AU/Malabo entries
  must be sourced from official AU pages.
- The checker is frozen; only the mapping mutates.
- Never silently drop a citation because it's stale — replace it with current
  law, or flag the gap explicitly.
- Keep going until every citation is `current`; log each update.
