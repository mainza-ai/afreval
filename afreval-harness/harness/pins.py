"""Pin records for the three frozen substrates.

The pins/*.yaml files are the ONLY place substrate versions are declared.
This module loads and validates them, and provides checksum tooling.
Bumping a pin is a deliberate, human-approved act (see scripts/bump_harness.py),
never an automatic update.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

PACKAGE_DIR = Path(__file__).resolve().parent
HARNESS_ROOT = PACKAGE_DIR.parent
PIN_DIR = HARNESS_ROOT / "pins"
CHECKSUM_DIR = HARNESS_ROOT / "checksums"

REQUIRED_KEYS: dict[str, list[str]] = {
    "afri_fertility.yaml": ["substrate", "pinned_version", "vendored_commit", "license"],
    "afrobench_lite.yaml": ["substrate", "variant", "vendored_commit", "harness_group"],
    "waxal.yaml": ["substrate", "hf_repo"],
}


class PinError(ValueError):
    pass


def _validate(slug: str, data: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_KEYS[slug] if k not in data]
    if missing:
        raise PinError(f"{slug}: missing required keys: {', '.join(missing)}")
    if data.get("status") == "pending-freeze":
        return
    checksums = data.get("checksums", [])
    if not isinstance(checksums, (list, dict)) or len(checksums) == 0:
        raise PinError(f"{slug}: checksums must be a non-empty list/dict once frozen")


def load_pin(slug: str) -> dict[str, Any]:
    """Load and validate one pin file (e.g. 'afri_fertility.yaml')."""
    path = PIN_DIR / slug
    if not path.exists():
        raise PinError(f"pin file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate(slug, data)
    return data


def load_all_pins() -> dict[str, dict[str, Any]]:
    return {p.name: load_pin(p.name) for p in sorted(PIN_DIR.glob("*.yaml"))}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def checksum_artifacts(entries: dict[str, str]) -> dict[str, str]:
    """Return {label: sha256} for artifact entries mapped to absolute paths.

    entries: {label: path-or-relpath-to-HARNESS_ROOT}. Raises FileNotFoundError
    if any artifact is missing — a missing artifact is a failed freeze.
    """
    result: dict[str, str] = {}
    for label, rel in entries.items():
        p = HARNESS_ROOT / rel
        if not p.is_file():
            raise FileNotFoundError(f"artifact missing for freeze: {rel}")
        result[label] = sha256_of(p)
    return result


def write_checksums(slug: str, checksums: dict[str, str], extra: dict[str, Any] | None = None) -> Path:
    """Persist a checksum manifest under checksums/ and return its path."""
    CHECKSUM_DIR.mkdir(exist_ok=True)
    doc = {"slug": slug, **({"extra": extra} if extra else {}), "files": checksums}
    out = CHECKSUM_DIR / f"{slug.replace('.yaml', '')}.sha256.yaml"
    out.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return out
