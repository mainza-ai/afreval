"""Language registry loaded from bundled languages.yaml."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

def _find_languages_file() -> Path:
    # Editable/source install: data/ is at project root (two levels above src/)
    candidate = Path(__file__).parents[2] / "data" / "languages.yaml"
    if candidate.exists():
        return candidate
    # Wheel install: data/ is bundled inside the package
    return Path(__file__).parent / "data" / "languages.yaml"


_LANGUAGES_FILE = _find_languages_file()


@dataclass(frozen=True)
class Language:
    iso639_3: str
    name: str
    family: str
    script: str
    tier: str
    flores_code: str
    sib200_code: str


@lru_cache(maxsize=1)
def _load() -> dict[str, Language]:
    data = yaml.safe_load(_LANGUAGES_FILE.read_text())
    return {
        entry["iso639_3"]: Language(**entry)
        for entry in data["languages"]
    }


def get(iso639_3: str) -> Language:
    registry = _load()
    try:
        return registry[iso639_3]
    except KeyError:
        raise KeyError(f"Language '{iso639_3}' not found. Available: {list_iso_codes()}")


def list_all() -> list[Language]:
    return list(_load().values())


def list_iso_codes() -> list[str]:
    return sorted(_load().keys())


def flores_code(iso639_3: str) -> str:
    return get(iso639_3).flores_code
