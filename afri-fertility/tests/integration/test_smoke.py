"""Integration smoke test: afri-fertility reproduce offline."""
import subprocess
import sys
from pathlib import Path

import pytest

AFRI_FERTILITY_ROOT = Path(__file__).parents[2]


def _run_cli(*args, cwd=None):
    # Try installed script first, fall back to python -m afri_fertility
    venv_bin = Path(sys.executable).parent
    cli_script = venv_bin / "afri-fertility"
    if cli_script.exists():
        cmd = [str(cli_script), *args]
    else:
        cmd = [sys.executable, "-m", "afri_fertility", *args]
    result = subprocess.run(
        cmd,
        cwd=cwd or AFRI_FERTILITY_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result


def test_cli_languages_list():
    result = _run_cli("languages", "list", "--json")
    assert result.returncode == 0
    import json
    langs = json.loads(result.stdout)
    assert len(langs) == 23
    iso_codes = {l["iso639_3"] for l in langs}
    assert "yor" in iso_codes
    assert "amh" in iso_codes
    assert "eng" in iso_codes


def test_cli_tokenizers_list():
    result = _run_cli("tokenizers", "list", "--json")
    assert result.returncode == 0
    import json
    toks = json.loads(result.stdout)
    ids = {t["id"] for t in toks}
    assert "openai/o200k_base" in ids
    assert "bigscience/bloom" in ids


def test_cli_corpora_list():
    result = _run_cli("corpora", "list", "--json")
    assert result.returncode == 0
    import json
    corpora = json.loads(result.stdout)
    ids = {c["id"] for c in corpora}
    assert "flores" in ids
    assert "sib200" in ids
    assert "mafand" in ids


def test_reproduce_exits_cleanly():
    """reproduce should either pass (with tokenizers) or warn (no tokenizers)."""
    result = _run_cli("reproduce")
    # Either succeeds (tokenizers available) or exits 1 with a clear message
    if result.returncode != 0:
        assert "No tokenizers available" in result.stdout or "No tokenizers available" in result.stderr
    else:
        # If it succeeds, must have printed some results
        assert "reproduce" in result.stdout.lower() or "PASS" in result.stdout
