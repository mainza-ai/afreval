---
type: strategy
tags: [regulation, au, malabo, kenya, nigeria, data-sovereignty, compliance]
updated: 2026-07-31
---

# Regulatory Landscape

AfrEval's ultimate strategic value proposition lies in aligning with the continent's rapidly evolving regulatory landscape — it acts as a **unified compliance engine**, transforming regulatory friction into a monetizable enterprise mechanism. The [compliance loop](../subsystems/compliance-loop.md) keeps the mapping current.

## AU Continental AI Strategy

- Adopted by the AU Executive Council in **July 2024** — positions Africa as a sovereign contributor to global AI development, not a passive consumer.
- Envisions AI contributing an estimated **$1.5 trillion to the African economy by 2030**.
- Highlights the **"development-governance paradox"**: tension between ambitious continental frameworks and severe constraints in local digital infrastructure, computational capacity, and state resource mobilization.
- Implementing it requires an estimated **$250–500 billion**; current commitments hover at **~$100–150 million**, concentrated in a few member states.

**AfrEval is the bridge:** a centralized, out-of-the-box evaluation and compliance API means governments don't build bespoke multi-billion-dollar testing infrastructures from scratch. It serves as delegated technological authority, verifying adherence to the AU's ethical-development, human-rights, and digital-sovereignty mandates — integrated with the AU Data Policy Framework and the **AfCFTA Protocol on Digital Trade**.

## Data sovereignty & localization

- **Malabo Convention** — continental legal baseline for cybersecurity and personal data protection; heavily influences national legislation.
- **Kenya** — Cloud Policy + Data Protection Act (ODPC); **Nigeria** — Data Protection Commission (NDPC) guidelines. Both enforce stringent localization: Top Secret/Secret data must be hosted/processed locally to avoid cross-border flow violations.
- Global frontier models often require sending data to external servers — violating these tenets.
- AfrEval certifies whether an agent's architecture allows **localized, on-premise, or sovereign-cloud deployment** without exposing protected data to foreign nodes, shielding clients from regulatory action and fines.

## Sovereignty caveat

Open-source ≠ sovereign-safe. Every component's network egress must be audited against local/on-prem requirements per deployment jurisdiction — including afri-fertility's own Hugging Face Hub dependency for tokenizer files ([risk register](../build-plan/risk-register.md)).

## Related

- [Compliance loop subsystem](../subsystems/compliance-loop.md) — the mechanism keeping this current
- [Enterprise SaaS & VC](enterprise-saas.md) — monetizing regulatory friction
- [Risk register — data sovereignty](../build-plan/risk-register.md)
- [Phases — Phase 5](../build-plan/phases.md)
