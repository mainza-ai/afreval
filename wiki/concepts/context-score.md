---
type: concept
tags: [context-score, core-ip, scoring, certification]
updated: 2026-07-31
---

# Context Score

AfrEval's **core intellectual property and operational output**. A deterministic composite rating, 0–100, that dictates whether an AI model is authorized to deploy within an enterprise or public-sector environment. If the score falls below the mandated regulatory or corporate threshold, the AfrEval API **blocks deployment entirely**, returning detailed telemetry so developers can do targeted supervised fine-tuning and resubmit.

## The three vectors

| Vector | Measures | Inputs |
|---|---|---|
| **Linguistic Fidelity** | Accuracy in processing regional data | WAXAL acoustic WER/CER + AfroBench task accuracy; weighted toward code-switching robustness (high-CMI naturalness) |
| **Cultural Safety & Alignment** | African-specific adversarial safety | BiasScope-corrected judge output; resistance to local sociopolitical manipulation, ethnic bias, regional legal adherence; penalizes uncertainty-driven leniency toward low-resource languages |
| **Structural Economics & Efficiency** | Financial sustainability of deployment | Inverse of token fertility premium from the [afri-fertility engine](../substrates/afri-fertility.md) (CPT/BPT, effective context window) |

## The weighting function

The final score is a weighted composite **tailored to the deploying industry**:

- A regional **telco** weights conversational fluidity and latency heavier.
- A commercial **bank** weights security and alignment heavier.

The weights live in per-vertical configs (`weights/{vertical}.yaml`) and are today presumably hand-set — which the [Context Score calibration loop](../subsystems/context-score-calibration.md) turns into a search problem. Threshold values are not yet specified anywhere (see [Synthesis](../synthesis.md)).

## Determinism & auditability

The score must be **reproducible**: same model + same weight config + same harness version → bit-identical score, always. This is enforced by keeping the [certification loop separate from the calibration loop](../subsystems/context-score-calibration.md) — certification is a deterministic pipeline invocation, never an agent-optimized search.

## Related

- [Subsystem: Context Score calibration](../subsystems/context-score-calibration.md) — the loop that tunes the weights
- [Substrates](../substrates/waxal.md) — the three frozen harnesses the score is computed against
- [African Language Tax](african-language-tax.md) — Structural Economics grounding
- [LLM-as-Judge Bias](llm-as-judge-bias.md) — Cultural Safety grounding
- [Code-Mixing](code-mixing.md) — Linguistic Fidelity grounding
- [Enterprise SaaS & VC](../strategy/enterprise-saas.md) — the score as the monetizable certification output
