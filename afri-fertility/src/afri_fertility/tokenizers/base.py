"""TokenizerAdapter protocol and registry."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TokenizerAdapter(Protocol):
    id: str
    family: str
    vocab_size: int | None
    inspectable: bool

    def count(self, text: str) -> int:
        """Return subword token count, excluding special/BOS/EOS tokens."""
        ...

    def tokens(self, text: str) -> list[str] | None:
        """Return token strings if inspectable, else None."""
        ...


class UnavailableAdapter:
    """Placeholder registered when a tokenizer fails to load."""

    def __init__(self, id: str, reason: str = "") -> None:
        self.id = id
        self.family = "unavailable"
        self.vocab_size = None
        self.inspectable = False
        self.reason = reason
        self.available = False

    def count(self, text: str) -> int:
        raise TokenizerUnavailableError(
            f"Tokenizer '{self.id}' is unavailable: {self.reason}"
        )

    def tokens(self, text: str) -> list[str] | None:
        raise TokenizerUnavailableError(
            f"Tokenizer '{self.id}' is unavailable: {self.reason}"
        )


class TokenizerUnavailableError(RuntimeError):
    pass


class TokenizerNotFoundError(KeyError):
    pass


class TokenizerRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, TokenizerAdapter | UnavailableAdapter] = {}

    def register(self, adapter: TokenizerAdapter | UnavailableAdapter) -> None:
        self._adapters[adapter.id] = adapter

    def get(self, id: str) -> TokenizerAdapter | UnavailableAdapter:
        try:
            return self._adapters[id]
        except KeyError:
            raise TokenizerNotFoundError(
                f"Tokenizer '{id}' not found. Available: {self.list_ids()}"
            )

    def list_ids(self) -> list[str]:
        return sorted(self._adapters.keys())

    def list_all(self) -> list[TokenizerAdapter | UnavailableAdapter]:
        return [self._adapters[k] for k in self.list_ids()]

    def available_ids(self) -> list[str]:
        return [k for k, v in self._adapters.items() if not isinstance(v, UnavailableAdapter)]


REGISTRY = TokenizerRegistry()
