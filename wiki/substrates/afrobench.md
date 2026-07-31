---
type: substrate
tags: [afrobench, benchmark, nlp, reasoning, evaluation, frozen-harness]
updated: 2026-07-31
---

# AfroBench

The **textual/reasoning substrate** for AfrEval. Built by McGill NLP because prior multilingual benchmarks (e.g. MEGA) exclude African languages due to data scarcity and low discoverability of existing datasets.

- **Source:** [McGill-NLP/AfroBench](https://github.com/McGill-NLP/AfroBench) (cloned locally at `../AfroBench/`) · leaderboard [mcgill-nlp.github.io/AfroBench](https://mcgill-nlp.github.io/AfroBench/) · paper [arXiv 2311.07978](https://arxiv.org/abs/2311.07978)
- **Coverage:** **64 African languages, 15 NLP tasks, 22 datasets** — classification, QA, reasoning, generation. Datasets on HuggingFace under the Masakhane AfroBench collection; runs via [LM-Harness](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/afrobench) (HF models) or `prompt_with_API` (closed models / TogetherAI).

## AfroBench-LITE

The compute-constrained variant — **7 datasets, 14 languages**. AfrEval defaults to this for routine/high-frequency certification passes, reserving full AfroBench for periodic deep audits (see [Context Score calibration cadence](../subsystems/context-score-calibration.md)).

## Empirical findings baked into AfrEval's scorer priors

- **Proprietary models lead on raw average score** (GPT-4o, Gemini 1.5 Pro).
- Among open models, **Gemma 2 27B leads and beats LLaMA 3.1 70B** despite ~half the parameters.
- **Fine-tuned baselines on AfroBench datasets often beat prompted general-purpose LLMs.**
- **Knowledge-intensive and reasoning tasks show the largest performance gap.**

This directly supports the Lugha-Llama finding (targeted adaptation beating scale — Princeton blog, [Lugha-Llama](https://blog.ai.princeton.edu/2025/04/22/lugha-llama-adapting-large-language-models-for-african-languages/)). The [Context Score](../concepts/context-score.md)'s Linguistic Fidelity vector is built to *reward* targeted adaptation — not penalize smaller specialized models relative to bigger generalists.

## Task mix

Includes machine translation, sentiment analysis, mathematical reasoning (**AfriMGSM**), natural language inference (**AfriXNLI**), and knowledge-based open-retrieval QA (**AfriQA**, **AfriMMLU**). Runs against LLMs and fine-tuned BERT/T5-style baselines.

## Use in AfrEval

- **Linguistic Fidelity** (textual component): task-specific accuracy from AfroBench / AfroBench-LITE in the scoring pipeline.
- The three scoring pipelines (WAXAL WER + AfroBench-LITE + afri-fertility) form the frozen harness of the [Context Score calibration loop](../subsystems/context-score-calibration.md).

## Related

- [WAXAL](waxal.md) — the acoustic substrate
- [Context Score — Linguistic Fidelity](../concepts/context-score.md)
- [Context Score calibration subsystem](../subsystems/context-score-calibration.md)
- [Phases — Phase 0](../build-plan/phases.md) — version pinning gate
