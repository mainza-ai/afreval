"""Unit tests for corpus loaders (network-free paths only)."""
import json
import tempfile
from pathlib import Path

import pytest

from afri_fertility.corpora.base import AlignmentError, _check_alignment
from afri_fertility.corpora.custom import CustomCorpus
from afri_fertility import languages


# --- alignment check ---

def test_alignment_ok():
    _check_alignment({"eng": ["a", "b"], "yor": ["x", "y"]})


def test_alignment_mismatch():
    with pytest.raises(AlignmentError, match="not equal"):
        _check_alignment({"eng": ["a", "b", "c"], "yor": ["x", "y"]})


# --- custom corpus JSONL ---

SAMPLE_JSONL = [
    {"id": "1", "domain": "health", "translations": {"eng": "Hello world", "yor": "Ẹ káàárọ̀"}},
    {"id": "2", "domain": "health", "translations": {"eng": "Good morning", "yor": "Ẹ káàárọ̀ bọ"}},
    {"id": "3", "domain": "finance", "translations": {"eng": "Save money", "yor": "Pàmọ́ owó"}},
]


@pytest.fixture
def jsonl_file(tmp_path):
    p = tmp_path / "test.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in SAMPLE_JSONL))
    return p


@pytest.fixture
def csv_file(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("id,domain,eng,yor\n1,health,Hello world,Ẹ káàárọ̀\n2,health,Good morning,Ẹ káàárọ̀ bọ\n")
    return p


def test_custom_jsonl_loads(jsonl_file):
    corpus = CustomCorpus(jsonl_file)
    result = corpus.load(["eng", "yor"])
    assert len(result["eng"]) == 3
    assert len(result["yor"]) == 3
    assert result["eng"][0] == "Hello world"


def test_custom_csv_loads(csv_file):
    corpus = CustomCorpus(csv_file)
    result = corpus.load(["eng", "yor"])
    assert len(result["eng"]) == 2
    assert result["yor"][1] == "Ẹ káàárọ̀ bọ"


def test_custom_missing_language(jsonl_file):
    corpus = CustomCorpus(jsonl_file)
    with pytest.raises(AlignmentError, match="languages not found"):
        corpus.load(["eng", "yor", "hau"])


def test_custom_languages_list(jsonl_file):
    corpus = CustomCorpus(jsonl_file)
    langs = corpus.languages()
    assert "eng" in langs
    assert "yor" in langs


def test_custom_domain_grouping(jsonl_file):
    corpus = CustomCorpus(jsonl_file)
    by_domain = corpus.load_with_domains(["eng", "yor"])
    assert "health" in by_domain
    assert "finance" in by_domain
    assert len(by_domain["health"]["eng"]) == 2
    assert len(by_domain["finance"]["eng"]) == 1


def test_custom_invalid_format(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("not a valid format")
    with pytest.raises(ValueError, match="Unsupported format"):
        CustomCorpus(p)


# --- language registry ---

def test_language_registry_loads():
    langs = languages.list_all()
    assert len(langs) == 23


def test_known_language():
    yor = languages.get("yor")
    assert yor.name == "Yoruba"
    assert yor.script == "Latin"
    assert yor.flores_code == "yor_Latn"


def test_unknown_language_raises():
    with pytest.raises(KeyError):
        languages.get("xyz")


def test_amharic_ethiopic():
    amh = languages.get("amh")
    assert amh.script == "Ethiopic"
    assert amh.flores_code == "amh_Ethi"


def test_english_baseline():
    eng = languages.get("eng")
    assert eng.tier == "baseline"


# --- reference suite file ---

def test_reference_suite_parseable():
    ref_file = Path(__file__).parents[2] / "data" / "reference_suite" / "reference.jsonl"
    assert ref_file.exists(), "reference.jsonl not found"
    records = [json.loads(line) for line in ref_file.read_text().splitlines() if line.strip()]
    assert len(records) >= 10
    for r in records:
        assert "id" in r
        assert "domain" in r
        assert "translations" in r
        assert "eng" in r["translations"]


def test_reference_suite_custom_corpus():
    ref_file = Path(__file__).parents[2] / "data" / "reference_suite" / "reference.jsonl"
    corpus = CustomCorpus(ref_file, corpus_id="reference")
    result = corpus.load(["eng", "yor", "swh", "amh"])
    assert len(result["eng"]) >= 10
    assert len(result["eng"]) == len(result["yor"])
