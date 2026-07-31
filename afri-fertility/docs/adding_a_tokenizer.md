# Adding a Tokenizer

This guide walks through adding a new tokenizer to `afri-fertility` so it appears in the registry, participates in study runs, and shows up in `afri-fertility tokenizers list`.

## How the registry works

Every tokenizer is a class that satisfies the `TokenizerAdapter` `typing.Protocol`:

```python
# src/afri_fertility/tokenizers/base.py
class TokenizerAdapter(Protocol):
    id:          str    # unique slug, e.g. "openai/o200k_base"
    family:      str    # e.g. "openai", "meta", "mistral"
    vocab_size:  int | None
    inspectable: bool   # True if token strings can be retrieved (not count-only)

    def count(self, text: str) -> int: ...
    def tokens(self, text: str) -> list[str]: ...
```

No inheritance needed — any object with these attributes and methods is a valid adapter.

Adapters are registered in the module-level `REGISTRY` singleton:

```python
from afri_fertility.tokenizers.base import REGISTRY
REGISTRY.register(my_adapter)
```

Auto-registration happens at import time by placing the `register()` call at module level in the adapter file, then importing that module from `__init__.py` or `cli.py`.

---

## Minimal example — a local SentencePiece model

```python
# src/afri_fertility/tokenizers/sp_adapter.py
from __future__ import annotations
import warnings
from afri_fertility.tokenizers.base import REGISTRY, UnavailableAdapter

class SPAdapter:
    """Wraps a SentencePiece model."""

    def __init__(self, id: str, model_path: str, family: str = "sentencepiece"):
        self.id = id
        self.family = family
        self.inspectable = True
        self._sp = None
        self._model_path = model_path

    @classmethod
    def load(cls, id: str, model_path: str) -> "SPAdapter":
        import sentencepiece as spm
        adapter = cls(id, model_path)
        sp = spm.SentencePieceProcessor()
        sp.Load(model_path)
        adapter._sp = sp
        adapter.vocab_size = sp.GetPieceSize()
        return adapter

    def count(self, text: str) -> int:
        return len(self._sp.EncodeAsIds(text))

    def tokens(self, text: str) -> list[str]:
        return self._sp.EncodeAsPieces(text)


# Auto-register at import time
try:
    adapter = SPAdapter.load(
        id="my-org/my-sp-model",
        model_path="/path/to/model.model",
    )
    REGISTRY.register(adapter)
except Exception as exc:
    warnings.warn(f"my-org/my-sp-model unavailable: {exc}", stacklevel=2)
    REGISTRY.register(UnavailableAdapter(id="my-org/my-sp-model"))
```

The `try/except` block is the **graceful degradation pattern** used throughout `afri-fertility`. If the model file is missing, the tokenizer registers as `UnavailableAdapter` and study runs skip it with a structured warning rather than crashing.

---

## Step-by-step guide

### 1. Pick a unique id

Use the format `<org>/<model-name>`. It must be unique in the registry. Check existing ids:

```bash
afri-fertility tokenizers list
```

### 2. Create the adapter class

Create a new file under `src/afri_fertility/tokenizers/` (or anywhere on your Python path). The class must implement:

| Attribute / Method | Type | Notes |
|---|---|---|
| `id` | `str` | Unique slug |
| `family` | `str` | Architecture family label |
| `vocab_size` | `int \| None` | `None` if unknown or count-only |
| `inspectable` | `bool` | `False` for API/count-only backends |
| `count(text: str) -> int` | method | Returns raw token count |
| `tokens(text: str) -> list[str]` | method | Returns token strings; may return `[]` if not `inspectable` |

### 3. Auto-register at import time

At the bottom of your module (or in a `register_all()` function you call from `__init__.py`):

```python
try:
    REGISTRY.register(MyAdapter.load(...))
except Exception as exc:
    warnings.warn(f"{adapter_id} unavailable: {exc}", stacklevel=2)
    REGISTRY.register(UnavailableAdapter(id=adapter_id))
```

### 4. Trigger the import

For the adapter to be registered when `afri-fertility` starts, it must be imported somewhere in the startup chain. The two natural places are:

**a) Inside `cli.py`** (if this tokenizer ships with the library):

```python
# src/afri_fertility/cli.py  — already imports tiktoken and HF adapters
import afri_fertility.tokenizers.sp_adapter  # noqa: F401
```

**b) In your application code** (if the adapter lives outside the library):

```python
import my_package.tokenizers.sp_adapter  # triggers auto-registration
from afri_fertility import run_study
```

### 5. Verify

```bash
afri-fertility tokenizers list
```

You should see the new id in the table, marked as `available` or `[unavailable]`.

```bash
afri-fertility measure \
  --text "Àwọn ará Nàìjíríà" \
  --lang yor \
  --models my-org/my-sp-model
```

### 6. Optional: add it to a study config

```yaml
# configs/my_study.yaml
tokenizers:
  - openai/o200k_base
  - my-org/my-sp-model
```

If the tokenizer is unavailable at run time, the runner logs it in `manifest.json` under `skipped_tokenizers` and continues with the rest.

---

## HuggingFace models

The existing `HFAdapter` in `src/afri_fertility/tokenizers/hf_adapter.py` handles most HF tokenizers. To add a new HF-hosted tokenizer, append an entry to `_HF_MODELS` in that file:

```python
_HF_MODELS = [
    # ... existing entries ...
    {
        "id":       "my-org/my-hf-model",
        "hf_repo":  "my-org/my-hf-model-tokenizer",
        "family":   "my-org",
    },
]
```

`register_all_hf()` (called at import time) iterates this list, applies the same graceful-degradation pattern, and registers each adapter. If a model requires a HuggingFace token:

```bash
export HF_TOKEN=hf_...
```

or pass `--hf-token` to any CLI command.

---

## Count-only (API) adapters

API backends that return token counts but not token strings set `inspectable = False` and return `[]` from `tokens()`. See `src/afri_fertility/tokenizers/api_adapter.py` (available under `afri-fertility[api]`) for the Claude and Gemini reference implementations. The key difference: `count()` makes a network call; caching is especially important.

---

## Adding prices for a new tokenizer

If the new tokenizer has API pricing and you want it to appear in cost calculations, add it to the price snapshot:

```yaml
# configs/prices_2026-06.yaml  (or create a new snapshot file)
models:
  my-org/my-sp-model:
    price_in:  0.000001   # USD per input token
    price_out: 0.000004   # USD per output token
```

Then point your study config at the updated snapshot:

```yaml
cost:
  prices: configs/prices_2026-06.yaml
```

---

## Running the tests

After adding a new adapter, add a golden-count test entry:

1. Run `tests/golden/generate_golden.py` to regenerate `golden_counts.json` (requires the tokenizer to be loadable):

   ```bash
   python tests/golden/generate_golden.py
   ```

2. Commit the updated `golden_counts.json`.

The test at `tests/golden/test_golden_counts.py` auto-skips adapters that are `UnavailableAdapter`, so CI stays green even without the model files.
