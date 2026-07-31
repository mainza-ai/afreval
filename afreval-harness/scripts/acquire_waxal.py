#!/usr/bin/env python3
"""§2.1.1 WAXAL acquisition & QA — steps 1–3 (Phase 0 blocking).

Ground truth, verified against the Hub (2026-07-31, repo sha e0a62aa):
  - google/WaxalNLP is organized per-language, per-task as configs
    ({lang}_asr, {lang}_tts). 19 languages publish an _asr config.
  - Each _asr config ships FOUR splits: train / validation / test (labeled —
    every row carries a 'transcription' field) plus a large 'unlabeled'
    split whose rows have transcription == "".
  - So transcribed-vs-untranscribed is separated BY SPLIT, not by a filter
    inside the labeled data. The paper's "~10% of collected audio was
    transcribed" describes pre-release collection; the untranscribed audio
    ships on the Hub as the unlabeled split.

Workflow implemented here:
  1. Pull per-language _asr configs, LABELED SPLITS ONLY (train+validation+test),
     scoped so *-unlabeled-* parquet shards are never downloaded.
  2. VERIFY empty/null transcriptions are (near-)absent in labeled splits;
     filter only the configs that actually need it. Don't assume.
  3. QA edit-distance pass is the REAL filter: a second-ASR re-transcription,
     per-clip edit distance vs the shipped transcription, flag/drop high-
     divergence rows AND unreadable/corrupted audio (per the galsenai/WaxalNLP
     community fork's experience).
  4. Checksum & freeze — scripts/freeze_checksums.py (step 4).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from harness.pins import sha256_of  # noqa: E402

EMPTY_TRANSCRIPTION_FILTER_THRESHOLD = 0.001  # >0.1% empties -> filter; below -> leave as-is, record only


def resolve_asr_configs(hf_repo: str, revision: str | None = None) -> list[str]:
    """Parse {lang}_asr configs from the dataset card's YAML frontmatter.

    The dataset API does not expose configs in metadata, so we parse the
    README's `configs:` block directly. Falls back to --languages offline.
    """
    try:
        from huggingface_hub import HfApi

        api = HfApi()
        readme = api.hf_hub_download(
            repo_id=hf_repo, filename="README.md", repo_type="dataset", revision=revision
        )
        text = Path(readme).read_text(encoding="utf-8")
        configs = re.findall(r"- config_name: (\S+_asr)\b", text)
        return sorted(set(configs))
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"[warn] could not resolve configs from dataset card ({exc}); use --languages", file=sys.stderr)
        return []


def audit_transcriptions(rows: list[dict], lang: str) -> tuple[dict, list[dict]]:
    """Step 2: verify empty/null transcriptions are rare in a LABELED split."""
    total = len(rows)
    empty = [r for r in rows if not (r.get("transcription") or "").strip()]
    rate = len(empty) / total if total else 0.0
    stats = {"language": lang, "total": total, "empty_or_null": len(empty), "empty_rate": round(rate, 6)}
    return stats, empty


def qa_edit_distance(rows: list[dict], second_pass: list[str], threshold: float = 0.4) -> list[dict]:
    """Step 3: flag rows where shipped transcription diverges from a second ASR pass.

    second_pass must align with rows (same order). Uses the deterministic
    WER from harness.waxal_eval.
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


def audio_integrity(rows: list[dict], limit: int | None = None) -> list[dict]:
    """Decode each clip's audio to catch unreadable/corrupted files (galsenai fork).

    Accessing example['audio'] triggers decode in the datasets audio feature;
    a decode failure is recorded as corrupt. limit=None -> check all rows.
    """
    checked, corrupt = [], []
    for i, row in enumerate(rows):
        if limit and i >= limit:
            break
        row = dict(row)
        try:
            _ = row["audio"]["array"] if isinstance(row.get("audio"), dict) and "array" in row["audio"] else row["audio"]
            checked.append({"idx": i, "id": row.get("id"), "ok": True})
        except Exception as exc:  # noqa: BLE001 - any decode failure is a corrupt file
            checked.append({"idx": i, "id": row.get("id"), "ok": False, "error": str(exc)})
            corrupt.append({"idx": i, "id": row.get("id"), "error": str(exc)})
    return checked, corrupt


def main() -> int:
    ap = argparse.ArgumentParser(description="WAXAL acquisition & QA (§2.1.1 steps 1-3)")
    ap.add_argument("--config", default=str(HARNESS_ROOT / "pins/waxal.yaml"), help="waxal pin file")
    ap.add_argument("--out", default=str(HARNESS_ROOT / "data/waxal"), help="output dir for the filtered corpus")
    ap.add_argument("--languages", nargs="*", help="explicit language set (ISO 639-3 codes, e.g. sna swa amh); overrides card resolution")
    ap.add_argument("--limit", type=int, help="cap rows per config (smoke test only — never freeze a limited pull)")
    ap.add_argument("--dry-run", action="store_true", help="resolve the plan and print it; do not download")
    ap.add_argument("--audio-check", action="store_true", help="decode clips to catch corrupted audio files")
    ap.add_argument("--audio-check-limit", type=int, default=200, help="rows to audio-check when --audio-check")
    args = ap.parse_args()

    pin = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if pin.get("status") == "frozen":
        print(f"[error] waxal pin is already frozen ({pin['pinned_version']}); a freeze bump is required to re-acquire", file=sys.stderr)
        return 1

    revision = pin.get("hf_revision") or None
    if args.languages:
        configs = sorted({f"{lang}_asr" for lang in args.languages})
    else:
        configs = resolve_asr_configs(pin["hf_repo"], revision)

    if args.dry_run:
        print(f"WAXAL acquisition plan for {pin['hf_repo']} (revision {revision or 'main'})")
        print(f"  labeled ASR configs ({len(configs)}): {', '.join(configs)}")
        print("  Step 1: pull LABELED splits only — load_dataset(split='train+validation+test');")
        print("          snapshot_download(allow_patterns='data/ASR/*/*-{train,validation,test}-*.parquet')")
        print("          -> *-unlabeled-* shards are never downloaded (transcribed/untranscribed are split-separated)")
        print("  Step 2: verify empty/null transcription rate per config (filter only if >0.1%)")
        print("  Step 3: QA edit-distance pass (second ASR) + audio-integrity check — the REAL filter")
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
        print(f"[1] pulling {cfg} (labeled splits only) ...")
        ds = load_dataset(pin["hf_repo"], cfg, revision=revision, split="train+validation+test")
        rows = list(ds)
        if args.limit:
            rows = rows[: args.limit]
        stats, empties = audit_transcriptions(rows, cfg)
        audit_log.append(stats)
        print(f"    {stats}")
        if stats["empty_rate"] > EMPTY_TRANSCRIPTION_FILTER_THRESHOLD:
            keep = [r for r in rows if (r.get("transcription") or "").strip()]
            print(f"    [filter] empty_rate above threshold; dropping {len(rows) - len(keep)} rows")
            rows = keep
        elif stats["empty_or_null"]:
            print(f"    [note] {stats['empty_or_null']} empty rows present but below threshold; recording only (do NOT assume)")

        if args.audio_check:
            checked, corrupt = audio_integrity(rows, limit=args.audio_check_limit)
            print(f"    [audio-check] {len(checked)} clips decoded, {len(corrupt)} corrupt/unreadable")
            (out / f"{cfg}_audio_check.json").write_text(json.dumps(corrupt, indent=2), encoding="utf-8")

        if args.limit:
            continue  # limited pulls are never persisted/frozen

        dest = out / f"{cfg}.jsonl"
        with open(dest, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"    wrote {len(rows)} rows -> {dest} (sha256={sha256_of(dest)[:16]}...)")

    (out / "transcription_audit.json").write_text(json.dumps(audit_log, indent=2), encoding="utf-8")
    print(f"[2] audit log -> {out / 'transcription_audit.json'}")
    print("[3] NOTE: run the second-ASR QA pass before freezing; see README 'WAXAL QA pass'")
    print("[done] acquisition complete. Run scripts/freeze_checksums.py to freeze (step 4).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
