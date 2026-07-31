# AfroBench
Large Scale Benchmark of Large Language Models on African Languages

AfroBench is an open, multilingual benchmark designed to evaluate Large Language Models (LLMs) across 64 African languages, 15 NLP tasks, and 22 datasets — covering classification, QA, reasoning, generation, and more.

This is the most comprehensive evaluation suite for African languages to date, created to address their persistent underrepresentation in mainstream NLP.

## Abstract
> Large-scale multilingual evaluations, such as MEGA, often include only a handful of African languages due to the scarcity of high-quality evaluation data and the limited discoverability of existing African datasets. This lack of representation hinders comprehensive LLM evaluation across a diverse range of languages and tasks. To address these challenges, we introduce AfroBench -- a multi-task benchmark for evaluating the performance of LLMs across 64 African languages, 15 tasks and 22 datasets. AfroBench consists of nine natural language understanding datasets, six text generation datasets, six knowledge and question answering tasks, and one mathematical reasoning task. We present results comparing the performance of prompting LLMs to fine-tuned baselines based on BERT and T5-style models. Our results suggest large gaps in performance between high-resource languages, such as English, and African languages across most tasks; but performance also varies based on the availability of monolingual data resources. Our findings confirm that performance on African languages continues to remain a hurdle for current LLMs, underscoring the need for additional efforts to close this gap.

Visit the HomePage: https://mcgill-nlp.github.io/AfroBench/

## 🤝 How to Contribute
We welcome contributions to the AfroBench Leaderboard!
### 👉 Run the evaluation
All scripts, prompts and datasets are opensource and available. We have 2 run options;
* Run with [LM-Harness](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/afrobench) - supports huggingface models.
* Run with [API](https://github.com/McGill-NLP/AfroBench/tree/main/prompt_with_API) - supports closed models and TogetherAI

### 👉 Submit your Results
* Format your results into a csv. Your results should include scores per language, per prompt per model.
* Open a pull request with your results
* We’ll review and integrate them into the official leaderboard

Join us in building more equitable and representative NLP benchmarks! We look forward to your contributions 🎉.

All dataset used in this benchmark are available at [huggingface](https://huggingface.co/collections/masakhane/afrobench-67dbf553ebf5701c2207f883)

### Citation

```
@misc{ojo2025afrobenchgoodlargelanguage,
      title={AfroBench: How Good are Large Language Models on African Languages?},
      author={Jessica Ojo and Odunayo Ogundepo and Akintunde Oladipo and Kelechi Ogueji and Jimmy Lin and Pontus Stenetorp and David Ifeoluwa Adelani},
      year={2025},
      eprint={2311.07978},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2311.07978},
}
```

Please cite datasets used. [Datasets Details](https://mcgill-nlp.github.io/AfroBench/tasks.html)