"""FLORES-200 parallel corpus loader."""
from __future__ import annotations

from .base import CORPUS_REGISTRY, AlignmentError, _check_alignment
from ..languages import flores_code, list_all as list_languages

# openlanguagedata/flores_plus is the actively maintained successor to facebook/flores.
# Fall back to facebook/flores if flores_plus is unavailable or missing a language.
_FLORES_HF_DATASET_PRIMARY = "openlanguagedata/flores_plus"
_FLORES_HF_DATASET_FALLBACK = "facebook/flores"
_SUPPORTED_SPLITS = ("dev", "devtest")


class Flores200Corpus:
    id: str = "flores"

    def languages(self) -> list[str]:
        return [lang.iso639_3 for lang in list_languages() if lang.flores_code]

    def load(self, languages: list[str], split: str = "devtest") -> dict[str, list[str]]:
        if split not in _SUPPORTED_SPLITS:
            raise ValueError(f"FLORES split must be one of {_SUPPORTED_SPLITS}, got '{split}'")

        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError("datasets package required: pip install datasets")

        import warnings

        result: dict[str, list[str]] = {}
        missing = []
        for iso in languages:
            try:
                fcode = flores_code(iso)
            except KeyError:
                missing.append(iso)
                continue

            try:
                try:
                    ds = load_dataset(_FLORES_HF_DATASET_PRIMARY, fcode, split=split, trust_remote_code=False)
                    text_field = "text"
                except Exception:
                    ds = load_dataset(_FLORES_HF_DATASET_FALLBACK, fcode, split=split, trust_remote_code=False)
                    text_field = "sentence"
                result[iso] = [row[text_field] for row in ds]
            except Exception as e:
                missing.append(iso)
                warnings.warn(f"FLORES: failed to load language '{iso}' ({fcode}): {e}")

        if missing:
            warnings.warn(f"FLORES: skipping {len(missing)} unavailable languages: {missing}")

        if not result:
            raise AlignmentError("FLORES: no languages could be loaded")

        _check_alignment(result)
        return result


CORPUS_REGISTRY.register(Flores200Corpus())
