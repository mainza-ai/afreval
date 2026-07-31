"""MAFAND-MT news corpus loader."""
from __future__ import annotations

from .base import CORPUS_REGISTRY, AlignmentError

_MAFAND_HF_DATASET = "masakhane/mafand"

# Language codes as used in MAFAND (lafand-mt) dataset.
# English-source pairs use "en-{3-letter-code}"; Wolof and Bambara are French-source.
# Study languages NOT in MAFAND (will be skipped with a warning — this is expected):
#   lin (Lingala), gaz (Oromo), sot (Sesotho), tir (Tigrinya), nqo (N'Ko), afr (Afrikaans)
#   eng / fra are source languages in MAFAND pairs, not targets — also skipped as expected.
_MAFAND_LANG_MAP = {
    "yor": "en-yor",
    "hau": "en-hau",
    "ibo": "en-ibo",
    "swh": "en-swa",
    "amh": "en-amh",
    "zul": "en-zul",
    "xho": "en-xho",
    "sna": "en-sna",
    "kin": "en-kin",
    "lug": "en-lug",
    "pcm": "en-pcm",
    "aka": "en-twi",
    "wol": "fr-wol",
    "bam": "fr-bam",
}


class MafandCorpus:
    id: str = "mafand"

    def languages(self) -> list[str]:
        return sorted(_MAFAND_LANG_MAP.keys())

    def load(self, languages: list[str], split: str = "test") -> dict[str, list[str]]:
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError("datasets package required: pip install datasets")

        import warnings

        result: dict[str, list[str]] = {}
        missing = []

        for iso in languages:
            mafand_code = _MAFAND_LANG_MAP.get(iso)
            if not mafand_code:
                missing.append(iso)
                continue

            try:
                ds = load_dataset(_MAFAND_HF_DATASET, mafand_code, split=split, trust_remote_code=True)
                src_lang, lang_key = mafand_code.split("-")
                result[iso] = [row["translation"][lang_key] for row in ds]
                # Store English source side for en-XXX pairs so the runner can compute
                # per-language premiums against the correct parallel English sentences.
                if src_lang == "en":
                    result[f"_eng_{iso}"] = [row["translation"]["en"] for row in ds]
            except Exception as e:
                missing.append(iso)
                warnings.warn(f"MAFAND: failed to load language '{iso}': {e}")

        if missing:
            warnings.warn(f"MAFAND: skipping {len(missing)} unavailable languages: {missing}")

        if not result:
            raise AlignmentError("MAFAND: no languages could be loaded")

        # MAFAND is bilingual (English-to-X pairs), not fully parallel across all languages,
        # so sentence counts can differ per language — no cross-language alignment check.
        return result


CORPUS_REGISTRY.register(MafandCorpus())
