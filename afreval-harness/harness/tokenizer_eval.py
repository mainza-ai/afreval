"""§3.1 frozen harness: script-stratified tokenizer evaluation.

Frozen substrate for the tokenizer & vocab search loop. Loads pinned parallel
corpora, re-tokenizes with a candidate vocab, and computes CPT/BPT/fertility/
premium per language and per script — Latin/Ge'ez(Ethiopic)/N'Ko stratified,
NEVER aggregated blind (§3.1 spec: "three numbers, not one").

The candidate tokenizer is injected as an adapter-like object with:
    .id      -> str
    .count(text: str) -> int          # tokens produced for text
afri-fertility's TokenizerAdapter instances satisfy this protocol; custom
candidates (BPE merge ordering, unigram, byte-fallback, script-aware
pre-tokenization) implement it in afreval-tokenizer-research.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import yaml

from .pins import PIN_DIR

BASELINE_LANGUAGE = "eng"

# Script classes required by §3.1 (independent scoring; a Latin win does not
# offset an N'Ko or Ethiopic regression).
LATIN = "latin"
ETHIOPIC = "ethiopic"
NKO = "nko"
OTHER = "other"
SCRIPT_CLASSES = (LATIN, ETHIOPIC, NKO, OTHER)

# Overrides / additions on top of the afri-fertility language registry.
# ISO 639-3 -> script class. Ethiopic = Ge'ez script family.
_SCRIPT_OVERRIDES: dict[str, str] = {
    "amh": ETHIOPIC,  # Amharic
    "tir": ETHIOPIC,  # Tigrinya
    "gez": ETHIOPIC,  # Ge'ez
    "nqo": NKO,       # N'Ko
}

_AFRI_LANGS_YAML = Path(__file__).resolve().parents[2] / "afri-fertility" / "data" / "languages.yaml"


def _load_afri_script_map() -> dict[str, str]:
    """Script map from the pinned afri-fertility language registry."""
    if not _AFRI_LANGS_YAML.exists():
        return {}
    data = yaml.safe_load(_AFRI_LANGS_YAML.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for entry in data.get("languages", []):
        script = (entry.get("script") or "").lower()
        iso = entry.get("iso639_3")
        if not iso:
            continue
        if "ethi" in script or "ge'ez" in script:
            mapping[iso] = ETHIOPIC
        elif "n'ko" in script or "nko" in script:
            mapping[iso] = NKO
        else:
            mapping[iso] = LATIN
    return mapping


_AFRI_SCRIPT_MAP = _load_afri_script_map()


def script_stratify(lang: str) -> str:
    """Classify an ISO 639-3 language code into latin | ethiopic | nko | other."""
    if lang in _SCRIPT_OVERRIDES:
        return _SCRIPT_OVERRIDES[lang]
    if lang in _AFRI_SCRIPT_MAP:
        return _AFRI_SCRIPT_MAP[lang]
    # Corpus codes like swh/swa/zul are Latin; unknown codes go to OTHER
    # rather than being guessed into a scored bucket.
    return OTHER


@dataclass(frozen=True)
class LanguageResult:
    lang: str
    script: str
    tokens: int
    words: int
    chars: int
    bytes: int
    fertility: float
    cpt: float
    bpt: float
    premium: float | None  # None for the baseline language

    def as_row(self) -> dict[str, Any]:
        return {
            "lang": self.lang,
            "script": self.script,
            "fertility": round(self.fertility, 4),
            "cpt": round(self.cpt, 4),
            "bpt": round(self.bpt, 4),
            "premium": round(self.premium, 4) if self.premium is not None else 1.0,
        }


@dataclass
class ScriptSummary:
    script: str
    languages: list[str] = field(default_factory=list)
    mean_fertility_premium: float | None = None  # mean of per-language premium
    mean_cpt: float | None = None
    mean_bpt: float | None = None


@dataclass
class TokenizerEvalResult:
    tokenizer: str
    baseline: str
    languages: list[LanguageResult] = field(default_factory=list)
    by_script: dict[str, ScriptSummary] = field(default_factory=dict)
    english_cpt: float | None = None

    def script_premiums(self) -> dict[str, float | None]:
        """The §3.1 headline: three numbers, one per scored script."""
        return {s: self.by_script[s].mean_fertility_premium for s in (LATIN, ETHIOPIC, NKO)}


def _aggregate_sum_then_divide(rows: list[LanguageResult], field_name: str) -> float:
    """Sum-then-divide over sentences (matches afri-fertility aggregation).

    rows must share the same denominators. We recompute from raw token/word/
    char/byte counts so aggregation is exact, not mean-of-ratios.
    """
    tokens = sum(r.tokens for r in rows)
    words = sum(r.words for r in rows)
    chars = sum(r.chars for r in rows)
    bytes_ = sum(r.bytes for r in rows)
    if field_name == "fertility":
        return tokens / words if words else 0.0
    if field_name == "cpt":
        return chars / tokens if tokens else 0.0
    if field_name == "bpt":
        return bytes_ / tokens if tokens else 0.0
    raise ValueError(field_name)


def english_cpt_regression(new_english_cpt: float, baseline_english_cpt: float, max_pct: float = 5.0) -> bool:
    """§3.1 constraint: regressing English CPT by more than max_pct fails the candidate."""
    if baseline_english_cpt <= 0:
        return True
    regression = (baseline_english_cpt - new_english_cpt) / baseline_english_cpt * 100.0
    return regression <= max_pct


class TokenizerEval:
    """Frozen §3.1 harness. Instantiate once per evaluation run."""

    def __init__(self, pin_slug: str = "afri_fertility.yaml", baseline: str = BASELINE_LANGUAGE):
        self.pin = yaml.safe_load((PIN_DIR / pin_slug).read_text(encoding="utf-8"))
        self.baseline = baseline
        if self.pin.get("status") != "frozen":
            raise ValueError(
                f"afri_fertility pin is not frozen ({self.pin.get('status')!r}); "
                "a non-frozen harness must not be used for scoring"
            )

    def evaluate(self, adapter: Any, corpus: dict[str, list[str]]) -> TokenizerEvalResult:
        """Score `adapter` over aligned sentences {lang: [sentences...]}.

        `adapter` needs `.id` and `.count(text) -> int`. Segmentation
        (words/chars/bytes) uses afri-fertility's pinned UAX-29-based routine
        for every tokenizer — registered adapters and custom §3.1 candidates
        are measured identically.
        """
        import unicodedata

        from afri_fertility.core.segmentation import segment

        langs = [l for l in corpus if corpus[l]]
        if self.baseline not in langs:
            raise ValueError(f"baseline language '{self.baseline}' missing from corpus")

        rows: list[LanguageResult] = []
        for lang in langs:
            tokens = words = chars = bytes_ = 0
            for sentence in corpus[lang]:
                normed = unicodedata.normalize("NFC", sentence)
                seg = segment(normed, normalization="")
                tokens += adapter.count(normed)
                words += seg.words
                chars += seg.chars
                bytes_ += seg.bytes
            rows.append(
                LanguageResult(
                    lang=lang,
                    script=script_stratify(lang),
                    tokens=tokens,
                    words=words,
                    chars=chars,
                    bytes=bytes_,
                    fertility=tokens / words if words else 0.0,
                    cpt=chars / tokens if tokens else 0.0,
                    bpt=bytes_ / tokens if tokens else 0.0,
                    premium=None,
                )
            )

        baseline_row = next(r for r in rows if r.lang == self.baseline)
        baseline_fertility = baseline_row.fertility

        # Frozen dataclass -> construct fresh rows with premium set.
        final = [
            LanguageResult(
                lang=r.lang, script=r.script, tokens=r.tokens, words=r.words,
                chars=r.chars, bytes=r.bytes, fertility=r.fertility, cpt=r.cpt,
                bpt=r.bpt,
                premium=(r.fertility / baseline_fertility) if (baseline_fertility and r.lang != self.baseline) else (1.0 if r.lang == self.baseline else None),
            )
            for r in rows
        ]

        result = TokenizerEvalResult(tokenizer=getattr(adapter, "id", type(adapter).__name__), baseline=self.baseline, languages=final)
        result.english_cpt = baseline_row.cpt

        for script in SCRIPT_CLASSES:
            members = [r for r in final if r.script == script]
            if not members:
                result.by_script[script] = ScriptSummary(script=script)
                continue
            premiums = [r.premium for r in members if r.premium is not None]
            result.by_script[script] = ScriptSummary(
                script=script,
                languages=[r.lang for r in members],
                mean_fertility_premium=sum(premiums) / len(premiums) if premiums else None,
                mean_cpt=_aggregate_sum_then_divide(members, "cpt"),
                mean_bpt=_aggregate_sum_then_divide(members, "bpt"),
            )
        return result


def load_reference_suite(path: Path | None = None) -> dict[str, list[str]]:
    """Load the pinned afri-fertility offline reference suite as a corpus.

    Aligned translations keyed by ISO 639-3, from
    afri-fertility/data/reference_suite/reference.jsonl.
    """
    if path is None:
        path = Path(__file__).resolve().parents[2] / "afri-fertility" / "data" / "reference_suite" / "reference.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"reference suite not found: {path}")
    corpus: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        for lang, text in record["translations"].items():
            corpus.setdefault(lang, []).append(text)
    return corpus
