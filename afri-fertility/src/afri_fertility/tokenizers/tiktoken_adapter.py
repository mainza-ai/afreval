"""Tiktoken adapters for OpenAI tokenizers (o200k_base, cl100k_base)."""
from __future__ import annotations

import warnings

import tiktoken

from .base import REGISTRY, UnavailableAdapter

_VOCAB_SIZES = {
    "o200k_base":     200019,
    "o200k_harmony":  201088,  # gpt-oss open-source models; same BPE text vocab as o200k_base + extra special tokens
    "cl100k_base":    100277,
}


class TiktokenAdapter:
    inspectable: bool = True
    family: str = "openai"

    def __init__(self, encoding_name: str) -> None:
        self._enc = tiktoken.get_encoding(encoding_name)
        self._encoding_name = encoding_name
        self.id = f"openai/{encoding_name}"
        self.vocab_size = _VOCAB_SIZES.get(encoding_name)

    def count(self, text: str) -> int:
        # disallowed_special=() so special tokens are not counted as special;
        # they're treated as plain text, consistent with "no BOS/EOS" requirement.
        return len(self._enc.encode(text, disallowed_special=()))

    def tokens(self, text: str) -> list[str]:
        token_ids = self._enc.encode(text, disallowed_special=())
        return [self._enc.decode([tid]) for tid in token_ids]


def _register_tiktoken(encoding_name: str) -> None:
    try:
        adapter = TiktokenAdapter(encoding_name)
        REGISTRY.register(adapter)
    except Exception as e:
        warnings.warn(
            f"Failed to load tiktoken encoding '{encoding_name}': {e}",
            stacklevel=2,
        )
        REGISTRY.register(UnavailableAdapter(id=f"openai/{encoding_name}", reason=str(e)))


_register_tiktoken("o200k_base")
_register_tiktoken("o200k_harmony")
_register_tiktoken("cl100k_base")
