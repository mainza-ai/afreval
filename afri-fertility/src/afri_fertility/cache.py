"""Disk and in-process caching for tokenizer objects and count results."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "afri_fertility"


def _cache_dir() -> Path:
    env = os.environ.get("AFRI_FERTILITY_CACHE_DIR")
    return Path(env) if env else _DEFAULT_CACHE_DIR


def _text_key(text: str, tokenizer_id: str, version: str = "1") -> str:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    safe_id = tokenizer_id.replace("/", "_")
    return f"{safe_id}__v{version}__{h}"


class CountCache:
    """Disk-backed count cache keyed by (sha256(text), tokenizer_id, version)."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._dir = (cache_dir or _cache_dir()) / "counts"
        self._dir.mkdir(parents=True, exist_ok=True)

    def get(self, text: str, tokenizer_id: str, version: str = "1") -> int | None:
        path = self._dir / (_text_key(text, tokenizer_id, version) + ".json")
        if path.exists():
            return json.loads(path.read_text())["count"]
        return None

    def set(self, text: str, tokenizer_id: str, count: int, version: str = "1") -> None:
        path = self._dir / (_text_key(text, tokenizer_id, version) + ".json")
        path.write_text(json.dumps({"count": count, "tokenizer_id": tokenizer_id}))


class TokenizerObjectCache:
    """In-process cache for loaded tokenizer adapter objects."""

    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    def get(self, id: str) -> object | None:
        return self._store.get(id)

    def set(self, id: str, adapter: object) -> None:
        self._store[id] = adapter


# Module-level singletons
COUNT_CACHE = CountCache()
OBJECT_CACHE = TokenizerObjectCache()
