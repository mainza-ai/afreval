---
type: build-plan
tags: [risks, mitigation, risk-register]
updated: 2026-07-31
---

# Risk Register

Risks beyond the platform caveat (which is covered under [Karpathy Loop — platform caveat](../concepts/karpathy-loop.md)).

| Risk | Mitigation |
|---|---|
| **Silent upstream drift** in WAXAL/AfroBench/afri-fertility invalidates historical scores | Phase 0 version pinning + documented, logged bump procedure; **never auto-update a harness dependency** |
| Autonomous calibration loop (§3.2) optimizes the *proxy* metric instead of real deployment safety — reproducing the exact LLM-as-judge failure mode the docs describe | Keep certification and calibration loops **structurally separate** ([§3.2.1](../subsystems/context-score-calibration.md)); require human sign-off before any calibration output reaches production weights |
| BiasScope loop (§3.3) burns judge-API budget with diminishing returns | Cost-bounded budget, not time-bounded; track marginal gap-increase per 100 calls and gate continued runs on it staying above a floor |
| `agent-airlock` fork drifts from upstream security patches | Track upstream releases explicitly — the project ships CVE-style presets reactively (e.g. Mobile MCP `mobile_open_url` scheme-validation preset). **Treat upstream release notes as a security feed, not a changelog** |
| Edge ASR results validated on datacenter hardware don't transfer to low-end mobile | Phase 4 acceptance criteria explicitly require **target-class hardware**, not proxy hardware ([§3.4](../subsystems/waxal-net.md)) |
| Data-sovereignty requirements (Malabo Convention, Kenya ODPC, Nigeria NDPC) conflict with components phoning home to US-based services — including afri-fertility's Hugging Face Hub dependency | Audit every component's network egress against local/on-prem requirements **per deployment jurisdiction** before certifying a client as compliant; don't assume a component is sovereign-safe just because it's open-source |
| Regulatory citations in the compliance loop (§3.6) go stale as AU/national frameworks evolve | Automated **citation-currency checks**, not a one-time compliance document ([§3.6](../subsystems/compliance-loop.md)) |
| Multi-GPU/production-scale search loops need orchestration the base fork lineage doesn't provide | Adopt `iii-hq/n-autoresearch`-style orchestration once any loop moves from "overnight research run" to "continuous production recalibration" — expected for §3.2's monthly-minimum cadence |

## Related

- [Phases](phases.md)
- [Regulatory Landscape](../strategy/regulatory-landscape.md) — data-sovereignty context
- [Synthesis](../synthesis.md) — open questions that are themselves risks
