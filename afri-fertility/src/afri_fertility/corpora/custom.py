"""Custom parallel corpus loader: JSONL and CSV formats (DLA vertical set)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterator

from .base import AlignmentError, _check_alignment


class CustomCorpus:
    """Load a custom parallel corpus from JSONL or CSV.

    JSONL format (one record per line):
        {"id": "h-0001", "domain": "health",
         "translations": {"eng": "...", "yor": "...", "hau": "..."}}

    CSV format:
        id,domain,eng,yor,hau,...
        h-0001,health,...
    """

    def __init__(self, path: str | Path, corpus_id: str = "custom") -> None:
        self.id = corpus_id
        self._path = Path(path)
        self._records: list[dict] = []
        self._load_file()

    def _load_file(self) -> None:
        suffix = self._path.suffix.lower()
        if suffix == ".jsonl":
            self._records = list(self._parse_jsonl(self._path))
        elif suffix == ".csv":
            self._records = list(self._parse_csv(self._path))
        else:
            raise ValueError(f"Unsupported format '{suffix}'. Use .jsonl or .csv")

    # Fields that are never language slots
    _NON_LANG_FIELDS = frozenset({
        "id", "domain", "source", "source_license", "status",
        "translation_methods", "features", "word_count", "created_at",
        "yor_mt", "yor_notes", "yor_codeswitches",
        "hau_mt", "hau_notes", "hau_codeswitches",
        "ibo_mt", "ibo_notes", "ibo_codeswitches",
        "swh_mt", "swh_notes", "swh_codeswitches",
        "amh_mt", "amh_notes", "amh_codeswitches",
        "wol_mt", "wol_notes", "wol_codeswitches",
    })

    @classmethod
    def _parse_jsonl(cls, path: Path) -> Iterator[dict]:
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if "translations" in record:
                        translations = record["translations"]
                    else:
                        # Flat format: language codes are top-level keys
                        translations = {
                            k: v for k, v in record.items()
                            if k not in cls._NON_LANG_FIELDS and isinstance(v, str) and v.strip()
                        }
                    yield {
                        "id": record.get("id", f"row-{i}"),
                        "domain": record.get("domain"),
                        "translations": translations,
                    }
                except (json.JSONDecodeError, KeyError) as e:
                    raise ValueError(f"Invalid JSONL at line {i}: {e}")

    @staticmethod
    def _parse_csv(path: Path) -> Iterator[dict]:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            lang_cols = [c for c in (reader.fieldnames or []) if c not in ("id", "domain")]
            for i, row in enumerate(reader, start=1):
                yield {
                    "id": row.get("id", f"row-{i}"),
                    "domain": row.get("domain"),
                    "translations": {lang: row[lang] for lang in lang_cols if row.get(lang)},
                }

    def languages(self) -> list[str]:
        if not self._records:
            return []
        return sorted(self._records[0]["translations"].keys())

    def load(self, languages: list[str], split: str = "all") -> dict[str, list[str]]:
        result: dict[str, list[str]] = {lang: [] for lang in languages}
        missing_langs: set[str] = set()

        for record in self._records:
            translations = record.get("translations", {})
            for lang in languages:
                if lang not in translations:
                    missing_langs.add(lang)
                else:
                    result[lang].append(translations[lang])

        if missing_langs:
            raise AlignmentError(
                f"Custom corpus: languages not found in data: {sorted(missing_langs)}"
            )

        _check_alignment(result)
        return result

    def load_with_domains(self, languages: list[str]) -> dict[str, dict[str, list[str]]]:
        """Load sentences grouped by domain: {domain: {lang: [sentences]}}."""
        by_domain: dict[str, list[dict]] = {}
        for record in self._records:
            domain = record.get("domain") or "general"
            by_domain.setdefault(domain, []).append(record)

        result = {}
        for domain, records in by_domain.items():
            lang_sents: dict[str, list[str]] = {lang: [] for lang in languages}
            for record in records:
                for lang in languages:
                    text = record["translations"].get(lang, "")
                    lang_sents[lang].append(text)
            result[domain] = lang_sents
        return result
