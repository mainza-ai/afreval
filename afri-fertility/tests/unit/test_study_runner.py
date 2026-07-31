"""Unit tests for study runner (no network, synthetic tokenizer + corpus)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from afri_fertility.config import StudyConfig
from afri_fertility.corpora.base import CORPUS_REGISTRY
from afri_fertility.tokenizers.base import REGISTRY, TokenizerRegistry
from afri_fertility.corpora.base import CorpusRegistry
from afri_fertility.study.runner import run_study, ResultRecord


# --- synthetic fixtures ---

class _FakeAdapter:
    """Returns fixed token count: len(text.split()) * 2 — simulates 2x fertility vs English."""
    def __init__(self, tok_id: str, multiplier: float = 2.0):
        self.id = tok_id
        self.family = "fake"
        self.vocab_size = 1000
        self.inspectable = True
        self._multiplier = multiplier

    def count(self, text: str) -> int:
        return max(1, int(len(text.split()) * self._multiplier))

    def tokens(self, text: str) -> list[str]:
        return text.split()


class _FakeCorpus:
    def __init__(self):
        self.id = "fake_corpus"

    def languages(self):
        return ["eng", "yor"]

    def load(self, languages, split="all"):
        data = {
            "eng": ["Hello world", "The quick brown fox", "Testing one two three"],
            "yor": ["Àwọn ará Nàìjíríà", "Ẹ káàárọ̀ o", "Tó ń gbé ní ìlú"],
        }
        return {lang: data[lang] for lang in languages if lang in data}


@pytest.fixture
def patched_registry(tmp_path, monkeypatch):
    """Monkeypatch REGISTRY and CORPUS_REGISTRY with fake adapters/corpus."""
    fake_reg = TokenizerRegistry()
    fake_reg.register(_FakeAdapter("fake/tok1", multiplier=1.0))
    fake_reg.register(_FakeAdapter("fake/tok2", multiplier=2.0))

    fake_corpus_reg = CorpusRegistry()
    fake_corpus_reg.register(_FakeCorpus())

    monkeypatch.setattr("afri_fertility.study.runner.REGISTRY", fake_reg)
    monkeypatch.setattr("afri_fertility.study.runner.CORPUS_REGISTRY", fake_corpus_reg)
    return tmp_path


def _make_config(tmp_path, tokenizers=None, languages=None):
    return StudyConfig(
        baseline_language="eng",
        languages=languages or ["eng", "yor"],
        corpora=[{"id": "fake_corpus", "split": "all"}],
        tokenizers=tokenizers or ["fake/tok1", "fake/tok2"],
        normalization="NFC",
        bootstrap={"iterations": 10, "seed": 42},
        output_dir=str(tmp_path / "runs"),
        workers=1,
    )


def test_run_produces_records(patched_registry):
    config = _make_config(patched_registry)
    result = run_study(config)
    assert len(result.records) > 0


def test_manifest_written(patched_registry):
    config = _make_config(patched_registry)
    result = run_study(config)
    manifest_path = Path(config.output_dir) / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert "timestamp" in manifest
    assert "n_records" in manifest


def test_baseline_premium_is_one(patched_registry):
    """English vs itself should yield premium ≈ 1.0."""
    config = _make_config(patched_registry)
    result = run_study(config)
    eng_records = [r for r in result.records if r.iso639_3 == "eng" and r.premium is not None]
    for r in eng_records:
        # eng premium against itself should be None (no baseline provided for eng)
        assert r.premium is None or abs(r.premium - 1.0) < 0.01


def test_yor_premium_computed(patched_registry):
    """Yoruba premium should be computed (not None) when baseline_sentences are available."""
    config = _make_config(patched_registry, tokenizers=["fake/tok2"])
    result = run_study(config)
    yor = [r for r in result.records if r.iso639_3 == "yor" and r.premium is not None]
    # Both languages get same multiplier → premium ≈ 1.0; at minimum it must be > 0
    assert len(yor) > 0
    assert all(r.premium > 0 for r in yor)


def test_dataframe_shape(patched_registry):
    config = _make_config(patched_registry)
    result = run_study(config)
    df = result.dataframe
    assert len(df) == len(result.records)
    assert "fertility" in df.columns
    assert "premium" in df.columns


def test_unavailable_tokenizer_skipped(patched_registry, tmp_path):
    from afri_fertility.tokenizers.base import UnavailableAdapter
    fake_reg = patched_registry
    # Re-patch with an unavailable tokenizer
    from afri_fertility.study.runner import REGISTRY as reg
    reg.register(_FakeAdapter("fake/tok1"))  # still have one available

    config = _make_config(patched_registry, tokenizers=["fake/tok1", "nonexistent/tok"])
    result = run_study(config)
    # Should still produce records from fake/tok1
    assert any(r.tokenizer == "fake/tok1" for r in result.records)


def test_config_from_yaml(tmp_path):
    yaml_content = """
baseline_language: eng
languages: [eng, yor]
corpora:
  - id: fake_corpus
    split: all
tokenizers:
  - fake/tok1
bootstrap:
  iterations: 10
  seed: 0
output_dir: runs/test
"""
    cfg_file = tmp_path / "test_config.yaml"
    cfg_file.write_text(yaml_content)
    config = StudyConfig.from_yaml(cfg_file)
    assert config.baseline_language == "eng"
    assert "yor" in config.languages
    assert config.bootstrap.seed == 0
