"""Study orchestrator: iterate corpus × language × tokenizer, aggregate, write results."""
from __future__ import annotations

import json
import logging
import unicodedata
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..config import StudyConfig
from ..core.aggregate import TextResult, aggregate_corpus
from ..core.segmentation import segment
from ..tokenizers import REGISTRY
from ..tokenizers.base import UnavailableAdapter, TokenizerUnavailableError
from ..corpora import CORPUS_REGISTRY
from ..corpora.base import AlignmentError
from .. import languages as lang_registry

logger = logging.getLogger(__name__)


@dataclass
class ResultRecord:
    corpus: str
    domain: str | None
    language: str
    iso639_3: str
    script: str
    family: str
    tokenizer: str
    vocab_size: int | None
    inspectable: bool
    n_sentences: int
    n_words: int
    n_tokens: int
    n_chars: int
    n_bytes: int
    fertility: float
    premium: float | None
    cpt: float
    bpt: float
    fertility_ci_low: float
    fertility_ci_high: float
    premium_ci_low: float | None
    premium_ci_high: float | None


@dataclass
class StudyResult:
    records: list[ResultRecord] = field(default_factory=list)
    manifest: dict = field(default_factory=dict)
    output_dir: Path = field(default_factory=lambda: Path("runs/main"))

    @property
    def dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(r) for r in self.records])

    def to_leaderboard(self) -> list[dict]:
        from ..report.leaderboard import records_to_leaderboard
        return records_to_leaderboard(self.records)

    def figures(self, outdir: str | Path | None = None) -> None:
        from ..report.figures import generate_all
        generate_all(self.dataframe, outdir or self.output_dir / "figures")


def _tokenize_sentence(text: str, adapter, normalization: str) -> tuple[int, int, int, int]:
    """Returns (tokens, words, chars, bytes) for one sentence."""
    if normalization:
        text = unicodedata.normalize(normalization, text)
    seg = segment(text, normalization="")  # already normalized
    n_tokens = adapter.count(text)
    return n_tokens, seg.words, seg.chars, seg.bytes


def _process_cell(
    corpus_id: str,
    domain: str | None,
    iso: str,
    lang_obj,
    sentences: list[str],
    baseline_sentences: list[str] | None,
    adapter,
    config: StudyConfig,
) -> ResultRecord | None:
    """Process one (corpus, domain, language, tokenizer) cell."""
    results = []
    for text in sentences:
        try:
            n_tokens, n_words, n_chars, n_bytes = _tokenize_sentence(
                text, adapter, config.normalization
            )
            results.append(TextResult(tokens=n_tokens, words=n_words, chars=n_chars, bytes=n_bytes))
        except TokenizerUnavailableError:
            return None
        except Exception as e:
            logger.warning(f"Error tokenizing sentence for {iso}/{adapter.id}: {e}")
            continue

    if not results:
        return None

    baseline_results = None
    if baseline_sentences:
        baseline_results = []
        for text in baseline_sentences:
            try:
                n_tokens, n_words, n_chars, n_bytes = _tokenize_sentence(
                    text, adapter, config.normalization
                )
                baseline_results.append(TextResult(tokens=n_tokens, words=n_words, chars=n_chars, bytes=n_bytes))
            except Exception:
                continue

    agg = aggregate_corpus(
        results,
        baseline_results=baseline_results,
        bootstrap_n=config.bootstrap.iterations,
        seed=config.bootstrap.seed,
    )

    return ResultRecord(
        corpus=corpus_id,
        domain=domain,
        language=lang_obj.name,
        iso639_3=iso,
        script=lang_obj.script,
        family=lang_obj.family,
        tokenizer=adapter.id,
        vocab_size=adapter.vocab_size,
        inspectable=adapter.inspectable,
        n_sentences=agg.n_sentences,
        n_words=agg.n_words,
        n_tokens=agg.n_tokens,
        n_chars=agg.n_chars,
        n_bytes=agg.n_bytes,
        fertility=agg.fertility,
        premium=agg.premium,
        cpt=agg.cpt,
        bpt=agg.bpt,
        fertility_ci_low=agg.fertility_ci.low,
        fertility_ci_high=agg.fertility_ci.high,
        premium_ci_low=agg.premium_ci.low if agg.premium_ci else None,
        premium_ci_high=agg.premium_ci.high if agg.premium_ci else None,
    )


def run_study(config: StudyConfig | str) -> StudyResult:
    """Run a complete study from config and return StudyResult."""
    if isinstance(config, str):
        config = StudyConfig.from_yaml(config)

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    skipped_tokenizers: list[str] = []
    all_records: list[ResultRecord] = []

    # Pre-validate tokenizers
    active_adapters = []
    for tok_id in config.tokenizers:
        try:
            adapter = REGISTRY.get(tok_id)
        except KeyError:
            warnings.warn(f"Tokenizer '{tok_id}' not in registry — skipping")
            skipped_tokenizers.append(tok_id)
            continue

        if isinstance(adapter, UnavailableAdapter):
            warnings.warn(f"Tokenizer '{tok_id}' unavailable ({adapter.reason}) — skipping")
            skipped_tokenizers.append(tok_id)
        else:
            active_adapters.append(adapter)

    if not active_adapters:
        warnings.warn("No tokenizers available. Study will produce no results.")

    # Process each corpus
    for corpus_spec in config.corpora:
        corpus = CORPUS_REGISTRY.get(corpus_spec.id)
        logger.info(f"Loading corpus {corpus_spec.id} split={corpus_spec.split}")

        try:
            sentences_by_lang = corpus.load(config.languages, split=corpus_spec.split)
            if config.max_sentences is not None:
                sentences_by_lang = {
                    key: sents[: config.max_sentences]
                    for key, sents in sentences_by_lang.items()
                }
        except AlignmentError as e:
            warnings.warn(f"Corpus {corpus_spec.id} alignment error: {e} — skipping corpus")
            continue
        except Exception as e:
            warnings.warn(f"Corpus {corpus_spec.id} load error: {e} — skipping corpus")
            continue

        baseline_sentences = sentences_by_lang.get(config.baseline_language)

        # Per-language baselines stored by corpus loaders (e.g. MAFAND stores
        # English source side as "_eng_{iso}" so premiums are computed against
        # the correct parallel English sentences for that specific language pair).
        per_lang_baselines = {
            iso: sentences_by_lang[f"_{config.baseline_language}_{iso}"]
            for iso in config.languages
            if f"_{config.baseline_language}_{iso}" in sentences_by_lang
        }

        futures = []
        with ThreadPoolExecutor(max_workers=config.workers) as pool:
            for iso in config.languages:
                if iso not in sentences_by_lang:
                    continue
                try:
                    lang_obj = lang_registry.get(iso)
                except KeyError:
                    lang_obj = type("L", (), {"name": iso, "script": "unknown", "family": "unknown"})()

                cell_baseline = per_lang_baselines.get(iso, baseline_sentences)

                for adapter in active_adapters:
                    f = pool.submit(
                        _process_cell,
                        corpus_spec.id,
                        None,
                        iso,
                        lang_obj,
                        sentences_by_lang[iso],
                        cell_baseline if iso != config.baseline_language else None,
                        adapter,
                        config,
                    )
                    futures.append(f)

            for f in as_completed(futures):
                try:
                    record = f.result()
                    if record is not None:
                        all_records.append(record)
                except Exception as e:
                    logger.error(f"Cell processing error: {e}")

    # Write manifest
    manifest = {
        "tool_version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_baseline": config.baseline_language,
        "n_languages": len(config.languages),
        "n_corpora": len(config.corpora),
        "n_tokenizers_requested": len(config.tokenizers),
        "n_tokenizers_active": len(active_adapters),
        "skipped_tokenizers": skipped_tokenizers,
        "normalization": config.normalization,
        "segmentation": config.segmentation,
        "bootstrap_n": config.bootstrap.iterations,
        "bootstrap_seed": config.bootstrap.seed,
        "n_records": len(all_records),
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    result = StudyResult(records=all_records, manifest=manifest, output_dir=output_dir)
    return result
