---
type: concept
tags: [code-mixing, code-switching, CMI, metrics, sociolinguistics]
updated: 2026-07-31
---

# Code-Mixing

Real-world communication across African digital ecosystems is heavily defined by **code-mixing / code-switching** — alternating between two or more languages within a single utterance (Nigerian Pidgin-English, Kenyan Sheng). Global models frequently classify these inputs as noisy or out-of-distribution. Code-mixing robustness is a weighted component of the Context Score's **Linguistic Fidelity** vector.

## Legacy baseline: the Code-Mixing Index (CMI)

CMI measures the ratio of token integration:

```
CMI = 1 - (W_major + N_li) / T_total
```

where `W_major` = words of the most prominent language, `T_total` = total tokens in the utterance, and `N_li` = language-independent tokens (named entities, abbreviations, user mentions).

## Enhanced CMI (AfrEval)

Traditional CMI only measures the proportional ratio of tokens — it fails to capture **syntactic validity or natural burstiness** of the language mix. AfrEval uses an advanced formulation incorporating the frequency of code alternation ("switch") points:

```
CMI_enhanced = α·(switch-point ratio per token) + β·(legacy ratio)   with α + β = 1
```

where the switch-point ratio is the number of alternation points per token.

## Companion indices

AfrEval tracks three quantities continuously:

- **CMI** (enhanced) — token integration with switch-point frequency.
- **Integration-index (I-index)** — approximates the probability that any given token in a corpus is a switch point.
- **Multilingual Index (M-index)** — measures inequality of language-tag distribution.

## How it's scored

Models that **regress to rigid, monolingual English grammar when prompted in conversational Swahili or Amharic** are heavily penalized. The Linguistic Fidelity vector rewards agents that synthesize and parse syntactically acceptable, naturalistic code-switched outputs.

## Status flag

The Research doc formalizes this math; the Bible only says Linguistic Fidelity is "weighted toward code-switching robustness" without the formulas. Whether CMI/I-index/M-index become a dedicated harness component is an open decision — see [Synthesis — open questions](../synthesis.md).

## Related

- [Context Score — Linguistic Fidelity](context-score.md)
- [WAXAL](../substrates/waxal.md) — acoustic analog: natural vs. scripted speech elicitation
- [Synthesis](../synthesis.md) — the code-mixing gap
