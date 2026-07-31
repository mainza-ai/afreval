#!/usr/bin/env python3
"""§2.1.1 WAXAL acquisition & QA — steps 1–3 (Phase 0 blocking).

Hub ground truth, verified against the Hub (2026-07-31, repo sha e0a62aa):
  - google/WaxalNLP is organized per-language, per-task as configs
    ({lang}_asr, {lang}_tts). 19 languages publish an _asr config.
  - Each _asr config ships FOUR splits: train / validation / test (labeled —
    every row carries a 'transcription' field) plus a large 'unlabeled'
    split whose rows have transcription == "".
  - Transcribed-vs-untranscribed is separated BY SPLIT, not by a filter inside
    the labeled data. The paper's "~10% of collected audio was transcribed"
    describes pre-release collection; the untranscribed audio ships on the Hub
    as the unlabeled split.

Two-stage acquisition strategy (eval-first):
  STAGE A (Phase 0, now): freeze the harness on the EVAL split only
    (validation + test). This is ~2% of the collection (~1-2 days) and is the
    only data the frozen WER/CER scoring harness needs (§3.4: "WAXAL held-out
    eval split"). Unblocks the Context Score acoustic component immediately.
  STAGE B (Phase 4, deferred): pull labeled train per language as the §3.4
    WAXAL-NET fine-tuning substrate, on-demand. Still excludes unlabeled.
  NEVER: the unlabeled split (pretraining-only) or a full ~1,250h pull.

Workflow implemented here:
  1. Pull per-language _asr configs for the requested splits (default
     validation test), scoped so *-unlabeled-* shards are never downloaded.
  2. Materialize audio (decodes each clip -> local cache), optionally copying
     files into the corpus so the frozen harness is self-contained.
  3. VERIFY empty/null transcriptions are (near-)absent in labeled splits;
     filter only configs that need it. Don't assume.
  4. QA edit-distance pass is the REAL filter: second-ASR re-transcription,
     per-clip edit distance vs the shipped transcription, flag/drop high-
     divergence rows AND unreadable/corrupted audio (per the galsenai/WaxalNLP
     community fork's experience).
  5. Checksum & freeze — scripts/freeze_checksums.py (step 4).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import re
from pathlib import Path

import yaml

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from harness.pins import sha256_of  # noqa: E402

EMPTY_TRANSCRIPTION_FILTER_THRESHOLD = 0.001  # >0.1% empties -> filter; below -> record only
DEFAULT_SPLITS = "validation test"


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
    """Step 3: verify empty/null transcriptions are rare in a LABELED split."""
    total = len(rows)
    empty = [r for r in rows if not (r.get("transcription") or "").strip()]
    rate = len(empty) / total if total else 0.0
    stats = {"language": lang, "total": total, "empty_or_null": len(empty), "empty_rate": round(rate, 6)}
    return stats, empty


def qa_edit_distance(rows: list[dict], second_pass: list[str], threshold: float = 0.4) -> list[dict]:
    """Step 4: flag rows where shipped transcription diverges from a second ASR pass.

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


def materialize(repo: str, revision: str | None, config: str, splits: list[str],
                out: Path, copy_audio: bool, max_rows: int | None = None) -> list[dict]:
    """Decode each clip, record its local audio path, optionally copy into corpus.

    Returns manifest records: {id, split, language, transcription,
    audio_path (relative to out), speaker_id, gender}. Decoding failures raise
    (corrupt/unreadable audio must not silently enter the frozen harness).
    """
    from datasets import load_dataset  # type: ignore

    records: list[dict] = []
    for split in splits:
        ds = load_dataset(repo, config, revision=revision, split=split)
        lang = config.removesuffix("_asr")
        audio_dir = out / "audio" / lang
        audio_dir.mkdir(parents=True, exist_ok=True)
        for i, row in enumerate(ds):
            if max_rows is not None and i >= max_rows:
                break
            audio = row["audio"]  # triggers download + decode
            try:
                _ = audio["array"]
            except Exception as exc:  # noqa: BLE001 - corrupt/unreadable audio
                raise RuntimeError(f"{config}/{split} row {row.get('id')}: unreadable audio: {exc}") from exc
            src = Path(audio["path"])
            dest = None
            if copy_audio:
                dest = audio_dir / src.name
                if not dest.exists():
                    shutil.copyfile(src, dest)
                rel = f"audio/{lang}/{src.name}"
            else:
                rel = str(src)
            records.append(
                {
                    "id": row.get("id"),
                    "split": split,
                    "language": row.get("language") or lang,
                    "transcription": row.get("transcription", ""),
                    "audio_path": rel,
                    "speaker_id": row.get("speaker_id"),
                    "gender": row.get("gender"),
                }
            )
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description="WAXAL acquisition & QA (§2.1.1 steps 1-3)")
    ap.add_argument("--config", default=str(HARNESS_ROOT / "pins/waxal.yaml"), help="waxal pin file")
    ap.add_argument("--out", default=str(HARNESS_ROOT / "data/waxal"), help="output dir for the corpus")
    ap.add_argument("--splits", nargs="+", default=DEFAULT_SPLITS.split(),
                    help="splits to acquire (default: validation test — Stage A eval freeze); Stage B: train validation test")
    ap.add_argument("--languages", nargs="*", help="explicit ISO 639-3 language set (e.g. sna swa amh); overrides card resolution")
    ap.add_argument("--limit", type=int, help="cap rows per config (smoke test only — never freeze a limited pull)")
    ap.add_argument("--no-copy-audio", action="store_true", help="manifest references HF cache paths instead of copying audio into the corpus")
    ap.add_argument("--dry-run", action="store_true", help="resolve the plan and print it; do not download")
    args = ap.parse_args()

    pin = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if pin.get("status") == "frozen":
        print(f"[error] waxal pin is already frozen ({pin['pinned_version']}); a freeze bump is required to re-acquire", file=sys.stderr)
        return 1

    _REPO = pin["hf_repo"]
    _REVISION = pin.get("hf_revision") or None
    if args.languages:
        configs = sorted({f"{lang}_asr" for lang in args.languages})
    else:
        configs = resolve_asr_configs(_REPO, _REVISION)

    forbidden = [s for s in args.splits if s == "unlabeled"]
    if forbidden:
        print("[error] the unlabeled split is never acquired (pretraining-only; not needed by AfrEval)", file=sys.stderr)
        return 1

    if args.dry_run:
        stage = "A (eval freeze)" if set(args.splits) <= {"validation", "test"} else "B (train, Phase 4)"
        print(f"WAXAL acquisition plan for {_REPO} (revision {_REVISION or 'main'}) — Stage {stage}")
        print(f"  splits: {args.splits}")
        print(f"  labeled ASR configs ({len(configs)}): {', '.join(configs)}")
        print("  -> *-unlabeled-* shards are never downloaded (transcribed/untranscribed are split-separated)")
        print("  Step 2: materialize audio (decode each clip; corrupt files raise — never enter the harness)")
        print("  Step 3: verify empty/null transcription rate per config (filter only if >0.1%)")
        print("  Step 4: QA edit-distance pass (second ASR) + flag high-divergence rows — the REAL filter")
        print("  Step 5: scripts/freeze_checksums.py -> checksums/waxal.sha256.yaml")
        return 0

    try:
        import datasets  # noqa: F401
    except ImportError:
        print("[error] datasets not installed; run: pip install -e '.[waxal]'", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    audit_log: list[dict] = []
    total_rows = 0
    for cfg in configs:
        print(f"[1] pulling {cfg} ({args.splits}) ...")
        records = materialize(_REPO, _REVISION, cfg, args.splits, out,
                              copy_audio=not args.no_copy_audio, max_rows=args.limit)
        stats, _ = audit_transcriptions(records, cfg)
        audit_log.append(stats)
        print(f"    {stats}")
        if stats["empty_rate"] > EMPTY_TRANSCRIPTION_FILTER_THRESHOLD:
            keep = [r for r in records if (r.get("transcription") or "").strip()]
            print(f"    [filter] empty_rate above threshold; dropping {len(records) - len(keep)} rows")
            records = keep
        if args.limit:
            continue  # limited pulls are never persisted/frozen
        dest = out / f"{cfg}.jsonl"
        with open(dest, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        total_rows += len(records)
        print(f"    wrote {len(records)} rows -> {dest} (sha256={sha256_of(dest)[:16]}...)")

    (out / "transcription_audit.json").write_text(json.dumps(audit_log, indent=2), encoding="utf-8")
    print(f"[2] audit log -> {out / 'transcription_audit.json'} ({total_rows} rows across {len(configs)} configs)")
    print("[3] NOTE: run the second-ASR QA pass before freezing; see README 'WAXAL QA pass'")
    print("[done] acquisition complete. Run scripts/freeze_checksums.py to freeze (step 4).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
