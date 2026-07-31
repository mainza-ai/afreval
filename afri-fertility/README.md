# afri-fertility

[![CI](https://github.com/ciphersenseai/afri-fertility/actions/workflows/ci.yml/badge.svg)](https://github.com/ciphersenseai/afri-fertility/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/afri-fertility)](https://pypi.org/project/afri-fertility/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-2606.24460-b31b1b)](https://arxiv.org/abs/2606.24460)
[![Dataset](https://img.shields.io/badge/HuggingFace-CipherSenseAI%2Fafri--fertility--results-ffd21e)](https://huggingface.co/datasets/CipherSenseAI/afri-fertility-results)
[![Leaderboard](https://img.shields.io/badge/Leaderboard-Token%20Fertility-orange)](https://datalens.africa/token-fertility-leaderboard)

**Measure the tokenization "tax" on African languages.**

Commercial LLMs bill, throttle, and context-budget per token. Because the same meaning takes more tokens in African languages than in English, speakers and builders face a structural cost, latency, and context penalty — before the model is even invoked. `afri-fertility` measures that penalty precisely.

It is the open measurement engine behind *[The African Language Tax](https://arxiv.org/abs/2606.24460)* paper, the public **[Token Fertility Leaderboard](https://datalens.africa/token-fertility-leaderboard)**, and the cost-calculator widget at datalens.africa.

```
afri-fertility reproduce
```
```
Tokenizer           Language  Fertility  Premium
──────────────────────────────────────────────────
openai/o200k_base   amh          8.500   7.83×
openai/o200k_base   yor          2.674   2.46×
openai/o200k_base   swh          1.800   1.66×
openai/o200k_base   fra          1.265   1.17×
```

---

## Install

```bash
pip install afri-fertility          # core: tiktoken + HF backends
pip install "afri-fertility[api]"   # + Claude / Gemini count-only
pip install "afri-fertility[viz]"   # + matplotlib figures
pip install "afri-fertility[dev]"   # + pytest, hypothesis
```

Requires Python 3.11+. The core path is CPU-only and key-free.

---

## Quickstart

### Single-text measurement

```python
from afri_fertility import measure_text

m = measure_text("Àwọn ará Nàìjíríà", tokenizer="openai/o200k_base")
print(f"tokens={m.tokens}  fertility={m.fertility:.2f}  cpt={m.cpt:.2f}")
# tokens=8  fertility=2.67  cpt=2.25
```

```bash
afri-fertility measure \
  --text "Àwọn ará Nàìjíríà tó ń gbé ní ìlú Èkó" \
  --lang yor \
  --models openai/o200k_base,openai/cl100k_base
```

### Cost calculator

```python
from afri_fertility import cost_of

results = cost_of("Àwọn ará Nàìjíríà", lang="yor", models=["openai/o200k_base"])
for r in results:
    print(f"{r.tokenizer}: ${r.total_cost_usd:.6f}  NGN {r.costs_local['NGN']:.4f}")
```

```bash
afri-fertility cost \
  --text "Àwọn ará Nàìjíríà" \
  --lang yor \
  --models openai/o200k_base,mistral/tekken \
  --currencies NGN,ZAR,KES
```

### Offline credibility demo

```bash
afri-fertility reproduce
```

Runs the bundled reference suite (10 parallel sentences, 7 languages) against all available tokenizers. No network, no API keys.

---

## Full study

Run the complete pre-registered study from the locked config:

```bash
afri-fertility run --config configs/study_main.yaml
```

Results land in `runs/main/`:

```
runs/main/
├── results.parquet / results.csv / results.json
├── leaderboard.json
├── manifest.json
└── figures/
    ├── fig1_heatmap.{png,svg}
    ├── fig2_premium_script.{png,svg}
    ├── fig3_cost.{png,svg}
    ├── fig4_context.{png,svg}
    ├── fig5_general_indomain.{png,svg}
    └── fig6_premium_accuracy.{png,svg}
```

For HF-gated tokenizers (Llama, Gemma, …):

```bash
afri-fertility run --config configs/study_main.yaml --hf-token $HF_TOKEN
# or: export HF_TOKEN=hf_... && afri-fertility run ...
```

---

## Python API

```python
from afri_fertility import measure_text, cost_of, run_study, load_tokenizer
from afri_fertility.config import StudyConfig

# Single-text metrics
m = measure_text("Ẹ káàbọ̀", tokenizer="openai/o200k_base")

# Widget backend: cost per model
results = cost_of("Ẹ káàbọ̀", lang="yor", models=["openai/o200k_base"])

# Full study
config = StudyConfig.from_yaml("configs/study_main.yaml")
result = run_study(config)

df = result.dataframe          # pandas DataFrame
result.figures("runs/figs")    # generate all 6 figures
lb = result.to_leaderboard()   # list[dict] for the frontend
```

---

## CLI reference

| Command | What it does |
|---|---|
| `afri-fertility measure` | Token count, fertility, CPT, BPT for input text |
| `afri-fertility cost` | Cost per model per language (widget backend) |
| `afri-fertility run` | Full study from YAML config |
| `afri-fertility figures` | Regenerate figures from an existing run |
| `afri-fertility leaderboard` | Emit leaderboard JSON from a run |
| `afri-fertility reproduce` | Offline reference suite — one-command credibility demo |
| `afri-fertility tokenizers list` | Registry of all tokenizers and their availability |
| `afri-fertility corpora list` | Registered corpus loaders |
| `afri-fertility languages list` | All 22 study languages with ISO codes and scripts |

Global flags: `--hf-token`, `--cache-dir`, `--log-level`, `--json`.

Full documentation: [docs/usage.md](docs/usage.md)

---

## Metrics

All metrics are computed on parallel corpora (same meaning, different languages), so the language effect is isolated from content.

| Metric | Formula | Meaning |
|---|---|---|
| **Fertility** `F(L,T)` | `tokens / words` | Tokens per word. Lower = more efficient. |
| **Premium** `P(L,T)` | `F(L,T) / F(eng,T)` | How many times more tokens L uses vs English. |
| **CPT** | `chars / tokens` | Characters packed per token. |
| **BPT** | `utf8_bytes / tokens` | Bytes per token (cross-script fair). |
| **Context efficiency** | `window_size × CPT` | Effective real chars in a fixed context window. |

Aggregation: **sum-then-divide** over all sentences (not mean-of-ratios). Bootstrap 95% CIs over sentences. Baseline: English. Normalization: NFC.

---

## Supported tokenizers

| Tokenizer id | Backend | Notes |
|---|---|---|
| `openai/o200k_base` | tiktoken | GPT-4o / GPT-4.1 / o-series |
| `openai/o200k_harmony` | tiktoken | OpenAI open-weight (gpt-oss) |
| `openai/cl100k_base` | tiktoken | GPT-3.5 / GPT-4 (legacy) |
| `meta/llama-3.1` | HF | Gated — needs `HF_TOKEN` |
| `meta/llama-4` | HF | Gated — needs `HF_TOKEN` |
| `google/gemma-4` | HF | Gated — needs `HF_TOKEN` |
| `mistral/tekken` | HF | |
| `qwen/qwen3` | HF | |
| `deepseek/v3` | HF | |
| `bigscience/bloom` | HF | Multilingual baseline |
| `cohere/aya-expanse` | HF | Multilingual-optimized baseline |
| `anthropic/claude` | API | `[api]` extra — count-only; needs `ANTHROPIC_API_KEY` |
| `google/gemini` | API | `[api]` extra — count-only; needs `GEMINI_API_KEY` |

Unavailable tokenizers are skipped with a warning; they never crash a run. See [docs/adding_a_tokenizer.md](docs/adding_a_tokenizer.md) to add your own.

---

## Supported languages

23 languages across 5 tiers:

**Core** (6): Yoruba · Hausa · Igbo · Wolof · Swahili · Amharic  
**Latin breadth** (11): Zulu · Xhosa · Shona · Kinyarwanda · Luganda · Akan/Twi · Lingala · Oromo · Nigerian Pidgin · Sesotho · Bambara  
**Non-Latin** (3): Tigrinya · Hausa-Ajami · N'Ko  
**Control** (1): Afrikaans  
**Baselines** (2): English · French

```bash
afri-fertility languages list
```

---

## Reproducing the paper numbers

```bash
git clone https://github.com/ciphersenseai/afri-fertility
cd afri-fertility
pip install -e ".[dev,viz]"
afri-fertility reproduce                                 # offline check, no keys
export HF_TOKEN=hf_...
afri-fertility run --config configs/study_main.yaml     # full locked study
afri-fertility figures --run runs/main
afri-fertility leaderboard --run runs/main --out leaderboard.json
```

All tokenizer versions, price snapshot date, FX rates, and config hash are recorded in `runs/main/manifest.json`.

The full results dataset from the paper is published at [CipherSenseAI/afri-fertility-results](https://huggingface.co/datasets/CipherSenseAI/afri-fertility-results) on HuggingFace.

---

## Project structure

```
afri-fertility/
├── src/afri_fertility/
│   ├── core/          # segmentation, metrics, aggregation (pure functions)
│   ├── tokenizers/    # tiktoken + HF + API adapters + registry
│   ├── corpora/       # FLORES-200, SIB-200, MAFAND-MT, custom JSONL/CSV
│   ├── cost/          # cost model, price/FX snapshots
│   ├── study/         # orchestrator, accuracy linkage
│   ├── report/        # tables, 6 figures, leaderboard JSON
│   ├── cli.py         # typer CLI
│   └── config.py      # pydantic StudyConfig
├── configs/           # locked study config + pinned price/FX snapshots
├── data/
│   ├── languages.yaml          # 22-language registry
│   └── reference_suite/        # offline reproduce dataset
└── tests/             # unit · golden · integration
```

---

## Citation

```bibtex
@misc{somide2026african,
  title         = {The African Language Tax: Quantifying the Cost, Latency,
                  and Context Penalty of Tokenizing African Languages in Frontier LLMs},
  author        = {Somide, Anthony Olaoye and {DataLens Africa Research}},
  year          = {2026},
  eprint        = {2606.24460},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL},
  url           = {https://arxiv.org/abs/2606.24460}
}
```

---

## License

Apache-2.0 · © 2026 DataLens Africa Research
