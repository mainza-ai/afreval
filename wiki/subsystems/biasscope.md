---
type: subsystem
tags: [biasscope, adversarial, llm-judge, probes, §3.3]
updated: 2026-07-31
---

# Subsystem §3.3 — BiasScope Adversarial Probe Discovery Loop

Defends the Cultural Safety vector by actively discovering judge-bias blind spots before they reach production. Grounding: [BiasScope](https://arxiv.org/html/2602.09383v1) (automated bias detection in LLM-as-a-Judge) and [LLM Evaluators are Biased across Languages](https://arxiv.org/html/2607.14480v1).

| Field | Spec |
|---|---|
| **Frozen harness** | The LLM-judge harness + low-resource-language corpus |
| **Mutable artifact** | The perturbation-generation strategy (an agent-editable "attack program") |
| **Instruction file** | `program.md`: *"maximize the induced pairwise-accuracy-vs-absolute-score-gap without the judge flagging the input as adversarial"* |
| **Metric** | Acceptance-rate delta across languages under the fixed decision threshold — the **43% gap** from the research is the existence proof that this metric is exploitable; treat it as the number to beat, in the defensive direction, over time |
| **Budget** | Fixed **number of judge API calls** per generation round, **not wall-clock** — this loop is cost-bound, since every iteration burns judge-model tokens |
| **Loop flavor** | `git commit`/revert style, cost-budgeted variant |
| **Language** | Python for agent loop + probe generation; Rust for the perturbation runtime if embedded in the sandboxed path (keeps adversarial-input-generation code physically separated from anything near production credentials) |
| **Repo** | `afreval-biasscope` |

## Why this loop matters

Pairwise accuracy is structurally blind to absolute-score drift — evaluators can clear 90%+ pairwise accuracy while showing up to a 43% acceptance-rate gap across languages under one global threshold ([llm-as-judge-bias](../concepts/llm-as-judge-bias.md)). BiasScope injects random cultural and linguistic biases combined with the target model's misjudgment self-explanations to uncover these blind spots.

## Related

- [LLM-as-Judge Bias](../concepts/llm-as-judge-bias.md) — the phenomenon being probed
- [Context Score — Cultural Safety](../concepts/context-score.md)
- [Karpathy Loop](../concepts/karpathy-loop.md) — cost-budgeted loop flavor
- [Risk register — judge-API budget burn](../build-plan/risk-register.md)
- [Phases — Phase 3](../build-plan/phases.md)
