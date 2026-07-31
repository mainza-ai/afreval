"""SIB-200 parallel corpus loader (robustness check corpus)."""
from __future__ import annotations

from .base import CORPUS_REGISTRY, AlignmentError, _check_alignment
from ..languages import list_all as list_languages

_SIB200_HF_DATASET = "Davlan/sib200"


class Sib200Corpus:
    id: str = "sib200"

    def languages(self) -> list[str]:
        return [lang.iso639_3 for lang in list_languages() if lang.sib200_code]

    def load(self, languages: list[str], split: str = "test") -> dict[str, list[str]]:
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError("datasets package required: pip install datasets")

        from ..languages import get as get_lang

        import warnings

        result: dict[str, list[str]] = {}
        missing = []

        for iso in languages:
            try:
                lang = get_lang(iso)
                sib_code = lang.sib200_code
            except KeyError:
                missing.append(iso)
                continue

            if not sib_code:
                missing.append(iso)
                continue

            try:
                ds = load_dataset(_SIB200_HF_DATASET, sib_code, split=split, trust_remote_code=False)
                result[iso] = [row["text"] for row in ds]
            except Exception as e:
                missing.append(iso)
                warnings.warn(f"SIB-200: failed to load language '{iso}' ({sib_code}): {e}")

        if missing:
            warnings.warn(f"SIB-200: skipping {len(missing)} unavailable languages: {missing}")

        if not result:
            raise AlignmentError("SIB-200: no languages could be loaded")

        _check_alignment(result)
        return result


CORPUS_REGISTRY.register(Sib200Corpus())
