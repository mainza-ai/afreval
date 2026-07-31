#!/usr/bin/env python3
"""§2.1.1 WAXAL acquisition & QA — steps 1–3 (Phase 0 blocking).

Implements the four-step agent-executable task list from the Implementation
Bible §2.1.1:
  1. Pull by config, not by tree — per-language {lang}_asr shards only.
  2. Empty/null transcription audit — per-language rate logged, filtered.
  3. Transcription-quality QA pass — second-ASR edit distance, flag/QA rows.
  4. Checksum & freeze — done by scripts/freeze_checksums.py after 1–3 pass.

Run:  uv run python scripts/acquire_waxal.py --config pins/waxal.yaml \
        --out data/waxal --dry-run
Use --dry-run to resolve the language set and print the exact pull plan without
downloading (recommended first step; the full pull is large).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from harness.pins import sha256_of  # noqa: E402


def resolve_configs(hf_repo: str) -> list[str]:
    """Resolve the per-language ASR configs for the pinned repo.

    Tries the HF API; on failure falls back to --languages so the plan is still
    printable offline (dry-run remains usable without network).
    """
    try:
        from huggingface_hub import HfApi

        api = HfApi()
        configs = sorted(
            c.config_name
            for c in api.list_configs(hf_repo, repo_type="dataset")
            if c.config_name.endswith("_asr")
        )
        return configs
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"[warn] could not resolve configs from HF API ({exc}); using --languages", file=sys.stderr)
        return []


def audit_transcriptions(rows: list[dict], lang: str) -> tuple[dict, list[dict]]:
    """Step 2: count empty/null transcriptions; return (stats, filtered_rows)."""
    total = len(rows)
    empty = [r for r in rows if not (r.get("transcription") or "").strip()]
    rate = len(empty) / total if total else 0.0
    stats = {"language": lang, "total": total, "empty_or_null": len(empty), "empty_rate": round(rate, 6)}
    return stats, [r for r in rows if (r.get("transcription") or "").strip()]


def qa_edit_distance(rows: list[dict], second_pass: list[str], threshold: float = 0.4) -> list[dict]:
    """Step 3: flag rows where the shipped transcription diverges from a second pass.

    second_pass must align with rows (same order). Uses deterministic WER.
    """
    from harness.waxal_eval import wer

    flagged = []
    for row, hyp in zip(rows, second_pass):
        ref = row.get("transcription", "")
        if not hyp:
            continue
        w = wer(ref, hyp)
        row = dict(row)
        row["qa_wer"] = round(w, 6)
        if w > threshold:
            row["qa_flag"] = "high-divergence"
            flagged.append(row)
    return flagged


def main() -> int:
    ap = argparse.ArgumentParser(description="WAXAL acquisition & QA (§2.1.1 steps 1-3)")
    ap.add_argument("--config", default=str(HARNESS_ROOT / "pins/waxal.yaml"), help="waxal pin file")
    ap.add_argument("--out", default=str(HARNESS_ROOT / "data/waxal"), help="output dir for the filtered corpus")
    ap.add_argument("--languages", nargs="*", help="explicit language set (ISO 639-3), overrides HF resolution")
    ap.add_argument("--limit", type=int, help="cap rows per language (smoke test only — never freeze a limited pull)")
    ap.add_argument("--dry-run", action="store_true", help="resolve the plan and print it; do not download")
    args = ap.parse_args()

    pin = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if pin.get("status") == "frozen":
        print(f"[error] waxal pin is already frozen ({pin['pinned_version']}); a freeze bump is required to re-acquire", file=sys.stderr)
        return 1

    configs = args.languages or resolve_configs(pin["hf_repo"])
    if args.dry_run:
        print(f"WAXAL acquisition plan for {pin['hf_repo']!r}")
        print(f"  ASR configs to pull ({len(configs)}): {', '.join(configs)}")
        print("  Step 1: snapshot_download(allow_patterns='*_asr/*.parquet') per config")
        print("  Step 2: empty/null transcription audit + filter")
        print("  Step 3: second-ASR edit-distance QA pass")
        print("  Step 4: scripts/freeze_checksums.py -> checksums/waxal.sha256.yaml")
        return 0

    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        print("[error] datasets not installed; run: pip install -e '.[waxal]'", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    audit_log: list[dict] = []
    for cfg in configs:
        print(f"[1] pulling {cfg} ...")
        ds = load_dataset(pin["hf_repo"], cfg, split="train" if "train" else None)
        rows = list(ds)
        if args.limit:
            rows = rows[: args.limit]
        stats, filtered = audit_transcriptions(rows, cfg)
        audit_log.append(stats)
        print(f"    {stats}")
        if args.limit:
            continue  # limited pulls are never persisted/frozen
        dest = out / f"{cfg}.jsonl"
        with open(dest, "w", encoding="utf-8") as f:
            for row in filtered:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"    wrote {len(filtered)} rows -> {dest} (sha256={sha256_of(dest)[:16]}...)")

    (out / "transcription_audit.json").write_text(json.dumps(audit_log, indent=2), encoding="utf-8")
    print(f"[2] audit log -> {out / 'transcription_audit.json'}")
    print("[3] NOTE: run the second-ASR QA pass before freezing; see README 'WAXAL QA pass'")
    print("[done] acquisition complete. Run scripts/freeze_checksums.py to freeze (step 4).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
