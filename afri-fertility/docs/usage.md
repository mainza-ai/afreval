# Usage Guide

## Contents

1. [Installation](#installation)
2. [Single-text measurement](#single-text-measurement)
3. [Cost calculator](#cost-calculator)
4. [Running the full study](#running-the-full-study)
5. [Understanding the output](#understanding-the-output)
6. [Regenerating figures](#regenerating-figures)
7. [Emitting the leaderboard](#emitting-the-leaderboard)
8. [Offline reproduce command](#offline-reproduce-command)
9. [Custom parallel corpus](#custom-parallel-corpus)
10. [Configuration reference](#configuration-reference)
11. [Python API reference](#python-api-reference)
12. [Caching](#caching)
13. [Environment variables](#environment-variables)

---

## Installation

```bash
pip install afri-fertility
```

The core install includes tiktoken and HuggingFace Transformers backends. No API keys are needed to use core tokenizers. For optional extras:

```bash
pip install "afri-fertility[api]"   # Claude and Gemini count-only backends
pip install "afri-fertility[viz]"   # matplotlib figures
pip install "afri-fertility[dev]"   # pytest, hypothesis (for contributors)
```

**Python 3.11+ required.** The core measurement path is CPU-only.

### HuggingFace-gated tokenizers

Some tokenizers (Llama 3.1, Gemma 2) require accepting a licence on HuggingFace and providing a token. Export it before running:

```bash
export HF_TOKEN=hf_...
```

Or pass it directly: `afri-fertility run --hf-token $HF_TOKEN`. Tokenizers that cannot load are skipped with a structured warning — they never crash a run.

---

## Single-text measurement

Measure the fertility and token count of any text against one or more tokenizers.

### CLI

```bash
afri-fertility measure \
  --text "Àwọn ará Nàìjíríà tó ń gbé ní ìlú Èkó" \
  --lang yor \
  --models openai/o200k_base,openai/cl100k_base,mistral/tekken
```

Output (rich table):

```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ Tokenizer          ┃ Tokens ┃ Words ┃ Fertility ┃ CPT   ┃ BPT   ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━┩
│ openai/o200k_base  │     14 │     7 │     2.000 │  2.86 │  3.57 │
│ openai/cl100k_base │     20 │     7 │     2.857 │  2.00 │  2.50 │
│ mistral/tekken     │     22 │     7 │     3.143 │  1.82 │  2.27 │
└────────────────────┴────────┴───────┴───────────┴───────┴───────┘
```

Add `--json` for machine-readable output:

```bash
afri-fertility measure --text "..." --models openai/o200k_base --json
```

### Python

```python
from afri_fertility import measure_text

m = measure_text(
    "Àwọn ará Nàìjíríà",
    tokenizer="openai/o200k_base",
    normalization="NFC",       # default
)

print(m.tokens)     # int: raw token count
print(m.words)      # int: UAX-29 word count
print(m.fertility)  # float: tokens / words
print(m.cpt)        # float: chars per token
print(m.bpt)        # float: UTF-8 bytes per token
```

---

## Cost calculator

Translate fertility into real cost for a reference workload of 1,000 English-word-equivalents, using pinned price and FX snapshots.

### CLI

```bash
afri-fertility cost \
  --text "Àwọn ará Nàìjíríà tó ń gbé ní ìlú Èkó" \
  --lang yor \
  --models openai/o200k_base,mistral/tekken \
  --out-in-ratio 1.0 \
  --currencies NGN,ZAR,KES
```

```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Tokenizer          ┃ Fertility ┃ Tokens ┃ USD/1k words ┃ NGN/1k words┃ ZAR/1k words┃ KES/1k words┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ openai/o200k_base  │     2.000 │   2000 │     0.025000 │    39.5000  │     0.4625  │     3.2500  │
└────────────────────┴───────────┴────────┴──────────────┴─────────────┴─────────────┴─────────────┘
```

### Python

```python
from afri_fertility import cost_of

results = cost_of(
    text="Àwọn ará Nàìjíríà",
    lang="yor",
    models=["openai/o200k_base"],
    out_in_ratio=1.0,
    local_currencies=["NGN", "ZAR", "KES"],
)

for r in results:
    print(r.tokenizer)
    print(f"  total USD: ${r.total_cost_usd:.6f}")
    print(f"  NGN:       ₦{r.costs_local['NGN']:.4f}")
    print(f"  relative:  {r.relative_cost:.3f}×")
```

### Cost model (pre-registered)

```
tokens(L,T)     = 1000 × F(L,T)
input_cost      = tokens × price_in(T)
output_cost     = tokens × out_in_ratio × price_out(T)
total_cost      = input_cost + output_cost
relative_cost   ≈ F(L,T) / F(eng,T)
```

Price and FX snapshots are in `configs/prices_2026-06.yaml` and `configs/fx_2026-06.yaml`. They are data, not code — update them for a new snapshot without touching logic.

---

## Running the full study

```bash
afri-fertility run --config configs/study_main.yaml
```

This runs the locked pre-registration study: all 22 languages × 4 corpora × 9 tokenizers. Expect it to take several minutes on a laptop (tiktoken-only path is fast; HF tokenizers add time per batch).

Progress is logged to the terminal. On completion:

```
Done. 792 records → runs/main
Manifest: runs/main/manifest.json
```

### Partial runs (subset of tokenizers/languages)

Create a custom config based on `configs/study_main.yaml`, overriding just the fields you want:

```yaml
# configs/quick.yaml
baseline_language: eng
languages: [eng, yor, amh]
corpora:
  - id: flores
    split: devtest
tokenizers:
  - openai/o200k_base
  - openai/cl100k_base
bootstrap:
  iterations: 100
  seed: 42
output_dir: runs/quick
```

```bash
afri-fertility run --config configs/quick.yaml
```

---

## Understanding the output

### `results.parquet` / `results.csv` / `results.json`

One row per `(corpus, domain, language, tokenizer)` cell:

| Column | Type | Description |
|---|---|---|
| `corpus` | str | Source corpus (`flores`, `sib200`, `mafand`, `custom`) |
| `domain` | str\|null | Domain for in-domain corpora (`health`, `finance`, `agri`) |
| `language` | str | Full language name |
| `iso639_3` | str | ISO 639-3 code |
| `script` | str | Script family (`Latin`, `Ethiopic`, `Arabic`, …) |
| `family` | str | Language family |
| `tokenizer` | str | Tokenizer id |
| `n_sentences` | int | Number of sentences in this cell |
| `n_tokens` | int | Total tokens (sum over all sentences) |
| `n_words` | int | Total words (UAX-29) |
| `fertility` | float | `n_tokens / n_words` |
| `premium` | float\|null | `fertility / baseline_fertility`; null for the baseline language |
| `cpt` | float | `n_chars / n_tokens` |
| `bpt` | float | `n_bytes / n_tokens` |
| `fertility_ci_low/high` | float | Bootstrap 95% CI bounds |
| `premium_ci_low/high` | float\|null | Bootstrap 95% CI bounds |

### `manifest.json`

Records everything needed for reproducibility:

```json
{
  "tool_version": "0.1.0",
  "timestamp": "2026-06-12T12:00:00+00:00",
  "n_languages": 22,
  "n_tokenizers_active": 3,
  "skipped_tokenizers": ["meta/llama-3.1", "google/gemma-2"],
  "normalization": "NFC",
  "segmentation": "uax29",
  "bootstrap_n": 1000,
  "bootstrap_seed": 42,
  "n_records": 264
}
```

### `leaderboard.json`

Array of records consumable by the datalens.africa frontend. One entry per `(language, tokenizer)` pair with fertility, premium, CPT, and cost in USD and local currencies.

---

## Regenerating figures

If you have a completed run and want to regenerate just the figures (e.g., after a style change):

```bash
afri-fertility figures --run runs/main
```

Figures are written to `runs/main/figures/` as both PNG and SVG.

The 6 pre-specified figures:

| Figure | What it shows | Tests |
|---|---|---|
| Fig 1 | Fertility heatmap (languages × tokenizers) | — |
| Fig 2 | Premium grouped by script | H1, H2 |
| Fig 3 | Cost per 1k words: best vs worst tokenizer | RQ5 |
| Fig 4 | Context-window efficiency vs English | RQ5 |
| Fig 5 | General vs in-domain premium | H4 |
| Fig 6 | Premium vs downstream accuracy scatter | H5 |

Fig 6 only renders when an accuracy CSV is provided via `accuracy_table` in the config (IrokoBench / AfroBench).

---

## Emitting the leaderboard

```bash
afri-fertility leaderboard --run runs/main --out leaderboard.json
```

The output is consumed directly by the datalens.africa leaderboard page. Schema per entry:

```json
{
  "language": "Yoruba",
  "iso639_3": "yor",
  "script": "Latin",
  "family": "Niger-Congo (Volta-Niger)",
  "tokenizer": "openai/o200k_base",
  "fertility": 2.4639,
  "premium": 2.2701,
  "cpt": 3.14,
  "cost_per_1k_usd": 0.0307,
  "cost_per_1k_ngn": 48.51,
  "cost_per_1k_zar": 0.568
}
```

---

## Offline reproduce command

```bash
afri-fertility reproduce
```

Runs the bundled reference suite (`data/reference_suite/reference.jsonl`) — 10 parallel sentences across 7 languages and 3 domains — against every tokenizer that is currently available. No network access, no API keys, no HF downloads needed for tiktoken.

Use this to:
- Verify the installation is working
- Confirm a tokenizer produces the expected fertility range
- Get a quick sense of the premium for core languages

Pass `--json` for scripted use:

```bash
afri-fertility reproduce --json | jq '.[] | select(.language == "yor")'
```

---

## Custom parallel corpus

Drop in your own parallel data using the JSONL or CSV format.

### JSONL format

```jsonl
{"id": "h-001", "domain": "health", "translations": {"eng": "The patient should rest.", "yor": "Aláìsàn yẹ kí ó sinmi.", "hau": "Majiyyaci ya kamata ya huta."}}
{"id": "f-001", "domain": "finance", "translations": {"eng": "Please enter your PIN.", "yor": "Jọ̀wọ́ tẹ nọ́mbà rẹ.", "hau": "Da fatan a shigar lambar PIN."}}
```

### CSV format

```csv
id,domain,eng,yor,hau
h-001,health,The patient should rest.,Aláìsàn yẹ kí ó sinmi.,Majiyyaci ya kamata ya huta.
```

### Using it

```python
from afri_fertility.corpora.custom import CustomCorpus

corpus = CustomCorpus("my_data.jsonl", corpus_id="dla_vertical")
sentences = corpus.load(["eng", "yor", "hau"])
by_domain = corpus.load_with_domains(["eng", "yor", "hau"])
```

To include it in a full study, add it to your config:

```yaml
# In your study config — custom corpora are loaded on-the-fly
# Add a custom runner step or use the Python API directly
```

---

## Configuration reference

Full schema for `study_main.yaml`:

```yaml
baseline_language: eng          # ISO 639-3 code of the premium denominator
languages:                      # list of ISO 639-3 codes
  - eng
  - yor
  - amh
  # ...

corpora:                        # list of corpus specs
  - id: flores
    split: devtest              # dev | devtest
  - id: sib200
    split: test
  - id: mafand
    split: test

tokenizers:                     # list of tokenizer ids from the registry
  - openai/o200k_base
  - bigscience/bloom

normalization: NFC              # NFC | NFD | NFKC | NFKD | "" (none)
segmentation: uax29             # uax29 | regex

bootstrap:
  iterations: 1000              # number of bootstrap resamples
  seed: 42                      # fixed seed for reproducibility

context_window: 128000          # tokens; used for context-efficiency metric

cost:
  prices: configs/prices_2026-06.yaml
  fx: configs/fx_2026-06.yaml
  reference_words: 1000         # workload size for cost computation
  scenarios:
    bank_cs:
      out_in_ratio: 1.0         # output tokens / input tokens
      monthly_queries: 1000000
    clinical_triage:
      out_in_ratio: 1.5
      monthly_queries: 200000

accuracy_table: null            # optional CSV for H5 premium↔accuracy join

output_dir: runs/main
workers: 4                      # thread-pool workers for tokenization
```

### Price snapshot schema (`configs/prices_*.yaml`)

```yaml
snapshot_date: "2026-06-12"
currency: USD
models:
  openai/o200k_base:
    price_in:  0.0000025    # USD per input token
    price_out: 0.000010     # USD per output token
```

### FX snapshot schema (`configs/fx_*.yaml`)

```yaml
snapshot_date: "2026-06-12"
base: USD
rates:
  NGN: 1580.0
  ZAR: 18.5
  KES: 130.0
```

To update prices or rates: create a new YAML file and point your config at it. Never edit existing snapshot files — they are the audit trail.

---

## Python API reference

### `measure_text`

```python
measure_text(
    text: str,
    tokenizer: str = "openai/o200k_base",
    normalization: str = "NFC",
) -> Metrics
```

Returns a `Metrics` object with fields: `tokens`, `words`, `chars`, `bytes`, `fertility`, `cpt`, `bpt`, `tokenizer`, `segmentation_method`.

### `cost_of`

```python
cost_of(
    text: str,
    lang: str = "eng",
    models: list[str] | None = None,       # default: all available
    prices: PriceTable | None = None,      # default: bundled snapshot
    fx: FXTable | None = None,             # default: bundled snapshot
    out_in_ratio: float = 1.0,
    local_currencies: list[str] | None = None,  # default: NGN, ZAR, KES
) -> list[CostResult]
```

Each `CostResult` has: `language`, `tokenizer`, `fertility`, `n_tokens`, `input_cost_usd`, `output_cost_usd`, `total_cost_usd`, `relative_cost`, `costs_local`.

### `run_study`

```python
run_study(config: StudyConfig | str) -> StudyResult
```

`StudyResult` exposes:
- `.dataframe` — `pd.DataFrame` of all `ResultRecord` rows
- `.manifest` — dict of run metadata
- `.to_leaderboard()` — `list[dict]`
- `.figures(outdir)` — generate all 6 figures

### `load_tokenizer`

```python
load_tokenizer(id: str) -> TokenizerAdapter
```

Returns the registered adapter for `id`. Raises `TokenizerNotFoundError` if not registered, `TokenizerUnavailableError` at call time if the adapter is registered but failed to load.

---

## Caching

Token counts are cached on disk at `~/.cache/afri_fertility/counts/` keyed by `sha256(text) + tokenizer_id + version`. Re-running the same study is fast after the first run.

Override the cache directory:

```bash
export AFRI_FERTILITY_CACHE_DIR=/path/to/cache
afri-fertility run --cache-dir /path/to/cache ...
```

---

## Environment variables

| Variable | Effect |
|---|---|
| `HF_TOKEN` | HuggingFace access token for gated models (Llama, Gemma) |
| `HF_ALLOW_REMOTE` | Set to any value to allow HF remote loading without a token |
| `TRANSFORMERS_OFFLINE` | Set to `1` to force fully offline HF mode |
| `AFRI_FERTILITY_CACHE_DIR` | Override the default disk-cache location |
| `ANTHROPIC_API_KEY` | Anthropic API key — enables `anthropic/claude` count-only adapter (`[api]` extra) |
| `GEMINI_API_KEY` | Google API key — enables `google/gemini` count-only adapter (`[api]` extra) |
| `GOOGLE_API_KEY` | Alias for `GEMINI_API_KEY` (either works) |
