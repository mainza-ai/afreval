---
type: subsystem
tags: [compliance, regulatory, citation, documentation, §3.6]
updated: 2026-08-07
---

# Subsystem §3.6 — Compliance & Documentation Loop

Maintains the mapping between AfrEval's certification output and each jurisdiction's actual legal requirements. Not in the original architecture sketch, but required by §5's regulatory-alignment goals — and "the difference between AfrEval being a real compliance layer and being a plausible-sounding one."

## Status: 100% citation currency (7/7 current)

`afreval-compliance/` (`citations/africa.yaml` + `check_currency.py`) verifies every citation resolves (HTTP 200) **and** contains its key phrase at the authoritative source. As of 2026-08-05 all seven are current: AU Continental AI Strategy (non-binding) + Malabo Convention (binding) + AfCFTA (binding) from official **au.int** pages, regional ECOWAS + SADC frameworks (non-binding), and Kenya ODPC + Nigeria NDPC. Every instrument carries a `binding`/`non-binding` flag surfaced by the checker so a strategy is never presented as law. A url left `TBD` is reported as **unverified** — never silently passing.

## The loop

A `git commit`/revert-style loop following the [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) `/autoresearch:docs`-equivalent pattern:

- **Frozen harness / ground truth:** current law as published by actual government sources (not a scrape of a scrape).
- **Mutable artifact:** the compliance mapping document (certification outputs → legal requirements per jurisdiction).
- **Metric:** automated **citation-currency check** — do the regulatory citations in the compliance mapping still resolve to current law?
- **Loop flavor:** `git commit`/revert style.

## Why it's low-glamour but load-bearing

Regulatory text changes. **A stale citation in a compliance report is a liability, not a rounding error.** The AU Continental AI Strategy, national data-protection laws, and regional frameworks are all evolving ([regulatory landscape](../strategy/regulatory-landscape.md)).

## Related

- [Regulatory Landscape](../strategy/regulatory-landscape.md) — AU AI Strategy, Malabo Convention, Kenya ODPC, Nigeria NDPC
- [Enterprise SaaS & VC](../strategy/enterprise-saas.md) — why compliance is the monetizable moat
- [Karpathy Loop](../concepts/karpathy-loop.md) — loop flavor
- [Risk register — stale citations](../build-plan/risk-register.md)
- [Phases — Phase 5](../build-plan/phases.md)
