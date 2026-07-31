#!/usr/bin/env python3
"""Freeze tooling — §2.1.1 step 4 / Phase 0 acceptance.

Generates checksum manifests for pinned artifacts and updates the pin files'
checksum records. This is the last step of any freeze or bump. It is the ONLY
path by which a pin becomes/stays 'frozen'.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from harness.pins import PIN_DIR, checksum_artifacts  # noqa: E402

# Artifacts per pin. Paths are relative to HARNESS_ROOT. Missing -> failed freeze.
ARTIFACTS: dict[str, dict[str, str]] = {
    "afri_fertility.yaml": {
        "afri_fertility_reference_suite": "../afri-fertility/data/reference_suite/reference.jsonl",
        "afri_fertility_languages_registry": "../afri-fertility/data/languages.yaml",
        "afri_fertility_study_config": "../afri-fertility/configs/study_main.yaml",
        "afri_fertility_prices_snapshot": "../afri-fertility/configs/prices_2026-06.yaml",
        "afri_fertility_fx_snapshot": "../afri-fertility/configs/fx_2026-06.yaml",
    },
    "afrobench_lite.yaml": {
        "afrobench_lite_group": "../AfroBench/lm-evaluation-harness/lm_eval/tasks/afrobench/afrobench-lite.yaml",
        "afrobench_main_group": "../AfroBench/lm-evaluation-harness/lm_eval/tasks/afrobench/afrobench.yaml",
        "afrobench_lite_prompt_configs": "../AfroBench/prompt_with_API/afrobench_lite",
    },
    "waxal.yaml": {
        # Populated after acquisition; the per-language filtered corpora and
        # the transcription audit log are checksummed at freeze time.
        "waxal_transcription_audit": "data/waxal/transcription_audit.json",
    },
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Freeze checksums for a pinned substrate")
    ap.add_argument("--pin", choices=list(ARTIFACTS), help="which pin to freeze")
    ap.add_argument("--all", action="store_true", help="freeze every pin")
    args = ap.parse_args()

    pins = list(ARTIFACTS) if args.all else ([args.pin] if args.pin else list(ARTIFACTS))

    for slug in pins:
        pin_path = PIN_DIR / slug
        pin = yaml.safe_load(pin_path.read_text(encoding="utf-8"))
        if pin.get("status") != "frozen" and slug != "waxal.yaml":
            print(f"[warn] {slug} status={pin.get('status')!r} — refusing to write checksums for a non-frozen pin", file=sys.stderr)
            continue

        # WAXAL: freeze the per-language corpora if present (globs), else only audit log.
        entries = dict(ARTIFACTS[slug])
        if slug == "waxal.yaml":
            corpus_dir = HARNESS_ROOT / "data/waxal"
            if corpus_dir.exists():
                for f in sorted(corpus_dir.glob("*_asr.jsonl")):
                    entries[f"waxal_{f.stem}"] = f"data/waxal/{f.name}"

        missing = []
        resolved: dict[str, str] = {}
        for label, rel in entries.items():
            if rel.endswith("afrobench_lite") or rel.endswith("afrobench_lite/"):
                files = sorted((HARNESS_ROOT / rel).glob("*.yaml"))
                for f in files:
                    resolved[f"afrobench_lite_{f.name}"] = f"../AfroBench/prompt_with_API/afrobench_lite/{f.name}"
                continue
            p = HARNESS_ROOT / rel
            if not p.exists():
                missing.append(rel)
            else:
                resolved[label] = rel
        if missing:
            print(f"[skip] {slug}: missing artifacts -> {missing}", file=sys.stderr)
            continue

        checksums = checksum_artifacts(resolved)
        pin["checksums"] = checksums
        pin_path.write_text(yaml.safe_dump(pin, sort_keys=False), encoding="utf-8")
        print(f"[frozen] {slug}: {len(checksums)} artifacts checksummed")
        for label, sha in sorted(checksums.items()):
            print(f"    {label}: {sha[:16]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
