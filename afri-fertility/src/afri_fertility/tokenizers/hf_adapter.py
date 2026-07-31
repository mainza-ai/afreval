"""HuggingFace tokenizer adapters (Llama, Gemma, Mistral, Qwen, DeepSeek, BLOOM, Aya)."""
from __future__ import annotations

import warnings
from dataclasses import dataclass

from .base import REGISTRY, UnavailableAdapter

_HF_MODELS: list[tuple[str, str, str]] = [
    # (adapter_id, hf_repo, family)
    ("meta/llama-3.1",    "meta-llama/Meta-Llama-3.1-8B",                   "meta"),
    ("meta/llama-4",      "meta-llama/Llama-4-Scout-17B-16E-Instruct",       "meta"),
    ("google/gemma-4",    "google/gemma-4-12B-it",                           "google"),
    # Tekken tokenizer (131k vocab) was introduced with Mistral Nemo (July 2024).
    # Mistral-7B-v0.3 uses the old 32k SentencePiece tokenizer and must NOT be used here.
    ("mistral/tekken",    "mistralai/Mistral-Nemo-Instruct-2407",            "mistral"),
    ("qwen/qwen3",        "Qwen/Qwen3-8B",                                   "qwen"),
    ("deepseek/v3",       "deepseek-ai/DeepSeek-V3",                         "deepseek"),
    ("bigscience/bloom",  "bigscience/bloom",                                "bigscience"),
    ("cohere/aya-expanse","CohereForAI/aya-expanse-8b",                      "cohere"),
]


class HFAdapter:
    family: str
    inspectable: bool = True

    def __init__(self, id: str, tokenizer, family: str) -> None:
        self.id = id
        self.family = family
        self._tokenizer = tokenizer
        self.vocab_size: int | None = getattr(tokenizer, "vocab_size", None)
        self.available = True

    def count(self, text: str) -> int:
        # encode without adding special tokens (no BOS/EOS)
        ids = self._tokenizer.encode(text, add_special_tokens=False)
        return len(ids)

    def tokens(self, text: str) -> list[str] | None:
        ids = self._tokenizer.encode(text, add_special_tokens=False)
        return self._tokenizer.convert_ids_to_tokens(ids)

    @classmethod
    def load(cls, id: str, hf_repo: str, family: str, token: str | None = None,
             force_local: bool = False) -> "HFAdapter":
        import os
        from transformers import AutoTokenizer

        offline = os.environ.get("TRANSFORMERS_OFFLINE", "0") == "1"
        allow_remote = (
            not force_local
            and not offline
            and (token is not None or bool(os.environ.get("HF_ALLOW_REMOTE", "")))
        )

        # Always try the local snapshot path first — reliable across transformers versions.
        # AutoTokenizer with local_files_only=True has inconsistencies; loading from the
        # resolved snapshot directory is the stable path.
        local_path = cls._resolve_local_snapshot(hf_repo)
        if local_path:
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    local_path, trust_remote_code=False, use_fast=True,
                )
                return cls(id=id, tokenizer=tokenizer, family=family)
            except Exception:
                pass  # snapshot found but load failed — fall through

        if not allow_remote:
            # force_local=True and not in cache → raise to mark as unavailable
            raise FileNotFoundError(f"Tokenizer not in local cache: {hf_repo}")

        # Not cached locally — download via network
        tokenizer = AutoTokenizer.from_pretrained(
            hf_repo,
            token=token,
            trust_remote_code=False,
            use_fast=True,
        )
        return cls(id=id, tokenizer=tokenizer, family=family)

    @staticmethod
    def _resolve_local_snapshot(hf_repo: str) -> str | None:
        """Return the local snapshot directory path if the model is cached, else None."""
        try:
            from huggingface_hub import snapshot_download
            path = snapshot_download(hf_repo, local_files_only=True)
            return path
        except Exception:
            pass
        # Fallback: scan the hub cache directory directly
        import os, glob as _glob
        slug = hf_repo.replace("/", "--")
        cache_root = os.environ.get(
            "HF_HUB_CACHE",
            os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub"),
        )
        pattern = os.path.join(cache_root, f"models--{slug}", "snapshots", "*", "tokenizer.json")
        matches = _glob.glob(pattern)
        if matches:
            return os.path.dirname(matches[0])
        return None


def _register_hf(id: str, hf_repo: str, family: str, token: str | None = None,
                 force_local: bool = False) -> None:
    try:
        adapter = HFAdapter.load(id, hf_repo, family, token=token, force_local=force_local)
        REGISTRY.register(adapter)
    except Exception as e:
        if not force_local:
            # Only warn when a network-allowed load fails — unexpected.
            # For force_local (cache-only), a miss is expected; table shows status.
            warnings.warn(
                f"HF tokenizer '{id}' ({hf_repo}) unavailable: {e}",
                stacklevel=2,
            )
        REGISTRY.register(UnavailableAdapter(id=id, reason=str(e)))


_hf_registered = False


def register_all_hf(hf_token: str | None = None, force_local: bool = False) -> None:
    """Register all HF adapters.

    force_local=True: fast path — only loads from disk cache, no network.
        Use for informational commands (tokenizers list). Does not set the
        idempotency flag so a later network-allowed call can still upgrade
        UnavailableAdapters to real ones.
    force_local=False (default): may use network if HF_ALLOW_REMOTE or HF_TOKEN
        is set. Sets the idempotency flag so subsequent calls are free.
    """
    global _hf_registered
    if _hf_registered:
        return
    for adapter_id, hf_repo, family in _HF_MODELS:
        _register_hf(adapter_id, hf_repo, family, token=hf_token, force_local=force_local)
    if not force_local:
        _hf_registered = True


def register_hf_by_ids(adapter_ids: list[str], hf_token: str | None = None,
                       force_local: bool = False) -> None:
    """Register only the specified HF adapters (by adapter id, e.g. 'mistral/tekken').
    Use this instead of register_all_hf when you know which tokenizers are needed.
    Skips adapters already registered as working (non-Unavailable) adapters.
    """
    id_map = {aid: (hf_repo, family) for aid, hf_repo, family in _HF_MODELS}
    for aid in adapter_ids:
        if aid not in id_map:
            continue  # not an HF adapter (e.g. tiktoken) — already registered
        # Skip if already loaded successfully — avoids redundant disk/network hits
        try:
            existing = REGISTRY.get(aid)
            if not isinstance(existing, UnavailableAdapter):
                continue
        except Exception:
            pass
        hf_repo, family = id_map[aid]
        _register_hf(aid, hf_repo, family, token=hf_token, force_local=force_local)


def _get_hf_token() -> str | None:
    import os
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
