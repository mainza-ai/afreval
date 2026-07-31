#!/usr/bin/env python3
"""§2.1.1 WAXAL acquisition & QA — steps 1–3 (Phase 0 blocking).

Hub ground truth, verified against the Hub (2026-07-31, repo sha e0a62aa):
  - google/WaxalNLP is organized per-language, per-task as configs
    ({lang}_asr, {lang}_tts). 19 languages publish an _asr config.
  - Each _asr config ships FOUR splits: train / validation / test (labeled —
    every row carries a 'transcription' field) plus a large 'unlabeled'
    split whose rows have transcription == "".
  - Audio bytes are EMBEDDED in the parquet files (struct<bytes, path>), so
    downloading a split's parquet IS downloading its audio. No separate fetch.
  - Transcribed-vs-untranscribed is separated BY SPLIT, not by a filter inside
    the labeled data. The paper's "~10% of collected audio was transcribed"
    describes pre-release collection.

IMPORTANT loader caveat: datasets.load_dataset() materializes the WHOLE
config (including unlabeled shards) even when you request one split. We
therefore do NOT use the loader — we snapshot_download with allow_patterns
scoped to the requested splits' parquet only, then read the local parquet
directly with pyarrow. This is what makes the eval-first strategy real:
Stage A downloads only validation+test (~6 GB for all 19 languages), never
train, never unlabeled, never TTS.

Two-stage acquisition strategy (eval-first):
  STAGE A (Phase 0, now): freeze the harness on the EVAL split only
    (validation + test) — the frozen WER/CER scoring harness (§3.4 "WAXAL
    held-out eval split").
  STAGE B (Phase 4, deferred): add labeled train per language as the §3.4
    WAXAL-NET fine-tuning substrate, on-demand.
  NEVER: the unlabeled split (pretraining-only; AfrEval does not pretrain)
    or a full ~1,250h pull.

Workflow:
  1. snapshot_download scoped to the requested splits (default validation test).
  2. Materialize: read local parquet, decode each clip (soundfile) — corrupt
     audio raises and never enters the harness — copy bytes to data/waxal/audio/.
  3. VERIFY empty/null transcriptions are (near-)absent in labeled splits;
     filter only configs that need it. Don't assume.
  4. QA edit-distance pass is the REAL filter: second-ASR re-transcription,
     per-clip edit distance vs shipped transcription, flag/drop high-divergence.
  5. Checksum & freeze — scripts/freeze_checksums.py.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import yaml

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from harness.pins import sha256_of  # noqa: E402

EMPTY_TRANSCRIPTION_FILTER_THRESHOLD = 0.001  # >0.1% empties -> filter; below -> record only
DEFAULT_SPLITS = ["validation", "test"]


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
        configs = set()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("- config_name:"):
                name = line.split(":", 1)[1].strip()
                if name.endswith("_asr"):
                    configs.add(name)
        return sorted(configs)
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"[warn] could not resolve configs from dataset card ({exc}); use --languages", file=sys.stderr)
        return []


def download_splits(hf_repo: str, revision: str, splits: list[str], raw_dir: Path) -> Path:
    """snapshot_download scoped to the requested splits' parquet only.

    allow_patterns match `data/ASR/*/*-{split}-*.parquet`; unlabeled/TTS/train
    (unless requested) are never fetched.
    """
    from huggingface_hub import snapshot_download  # type: ignore

    patterns = [f"data/ASR/*/*-{s}-*.parquet" for s in splits]
    return Path(
        snapshot_download(
            repo_id=hf_repo,
            repo_type="dataset",
            revision=revision,
            allow_patterns=patterns,
            local_dir=str(raw_dir),
        )
    )


def materialize(raw_dir: Path, config: str, splits: list[str],
                out: Path, max_rows: int | None = None) -> list[dict]:
    """Read local parquet, decode+copy audio, return manifest records.

    Records: {id, split, language, transcription, audio_path, speaker_id,
    gender}. Corrupt/unreadable audio raises — it must not silently enter the
    frozen harness (per the galsenai/WaxalNLP fork's experience).
    """
    import pyarrow.parquet as pq  # type: ignore
    import soundfile as sf  # type: ignore

    lang = config.removesuffix("_asr")
    lang_dir = raw_dir / "data/ASR" / lang
    audio_dir = out / "audio" / lang
    audio_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    for split in splits:
        files = sorted(lang_dir.glob(f"*-{split}-*.parquet"))
        if not files:
            print(f"    [warn] no {split} parquet for {config}; skipping split")
            continue
        table = pq.read_table(files)
        cols = {name: table.column(name).to_pylist() for name in table.column_names}
        n = table.num_rows
        for i in range(n):
            if max_rows is not None and i >= max_rows:
                break
            audio = cols["audio"][i]
            raw_bytes = (audio or {}).get("bytes")
            if not raw_bytes:
                raise RuntimeError(f"{config}/{split} row {cols['id'][i]}: audio bytes missing")
            try:
                sf.read(io.BytesIO(raw_bytes))  # decode check
            except Exception as exc:  # noqa: BLE001 - corrupt/unreadable
                raise RuntimeError(f"{config}/{split} row {cols['id'][i]}: unreadable audio: {exc}") from exc
            fname = f"{cols['id'][i]}.mp3"
            dest = audio_dir / fname
            if not dest.exists():
                dest.write_bytes(raw_bytes)
            records.append(
                {
                    "id": cols["id"][i],
                    "split": split,
                    "language": cols.get("language", [lang] * n)[i] or lang,
                    "transcription": cols["transcription"][i],
                    "audio_path": f"audio/{lang}/{fname}",
                    "speaker_id": cols.get("speaker_id", [None] * n)[i],
                    "gender": cols.get("gender", [None] * n)[i],
                }
            )
    return records


def audit_transcriptions(records: list[dict], lang: str) -> dict:
    """Step 3: verify empty/null transcriptions are rare in a LABELED split."""
    total = len(records)
    empty = [r for r in records if not (r.get("transcription") or "").strip()]
    rate = len(empty) / total if total else 0.0
    return {"language": lang, "total": total, "empty_or_null": len(empty), "empty_rate": round(rate, 6)}


def qa_edit_distance(records: list[dict], second_pass: list[str], threshold: float = 0.4) -> list[dict]:
    """Step 4: flag rows where shipped transcription diverges from a second ASR pass.

    second_pass must align with records (same order). Uses the deterministic
    WER from harness.waxal_eval.
    """
    from harness.waxal_eval import wer

    flagged = []
    for row, hyp in zip(records, second_pass):
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
    ap.add_argument("--out", default=str(HARNESS_ROOT / "data/waxal"), help="output dir for the corpus")
    ap.add_argument("--splits", nargs="+", default=DEFAULT_SPLITS,
                    help="splits to acquire (default: validation test — Stage A eval freeze); Stage B: train validation test")
    ap.add_argument("--languages", nargs="*", help="explicit ISO 639-3 language set (e.g. sna swa amh); overrides card resolution")
    ap.add_argument("--limit", type=int, help="cap rows per config (smoke test only — never freeze a limited pull)")
    ap.add_argument("--dry-run", action="store_true", help="resolve the plan and print it; do not download")
    args = ap.parse_args()

    pin = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if pin.get("status") == "frozen":
        print(f"[error] waxal pin is already frozen ({pin['pinned_version']}); a freeze bump is required to re-acquire", file=sys.stderr)
        return 1

    if "unlabeled" in args.splits:
        print("[error] the unlabeled split is never acquired (pretraining-only; not needed by AfrEval)", file=sys.stderr)
        return 1

    repo = pin["hf_repo"]
    revision = pin.get("hf_revision") or None
    if args.languages:
        configs = sorted({f"{lang}_asr" for lang in args.languages})
    else:
        configs = resolve_asr_configs(repo, revision)

    stage = "A (eval freeze)" if set(args.splits) <= {"validation", "test"} else "B (train, Phase 4)"
    if args.dry_run:
        print(f"WAXAL acquisition plan for {repo} (revision {revision or 'main'}) — Stage {stage}")
        print(f"  splits: {args.splits}")
        print(f"  labeled ASR configs ({len(configs)}): {', '.join(configs)}")
        print("  download: snapshot_download(allow_patterns='data/ASR/*/*-{split}-*.parquet')")
        print("    -> never unlabeled/TTS/other splits; audio is embedded in the parquet")
        print("  Step 2: materialize audio (decode each clip; corrupt files raise — never enter the harness)")
        print("  Step 3: verify empty/null transcription rate per config (filter only if >0.1%)")
        print("  Step 4: QA edit-distance pass (second ASR) + flag high-divergence rows — the REAL filter")
        print("  Step 5: scripts/freeze_checksums.py -> checksums/waxal.sha256.yaml")
        return 0

    try:
        import huggingface_hub  # noqa: F401
        import pyarrow  # noqa: F401
        import soundfile  # noqa: F401
    except ImportError as exc:
        print(f"[error] missing dependency: {exc}; run: pip install -e '.[waxal]'", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "raw"

    print(f"[1] downloading {', '.join(args.splits)} splits for {len(configs)} configs (no unlabeled, no TTS) ...")
    download_splits(repo, revision, args.splits, raw_dir)

    audit_log: list[dict] = []
    total_rows = 0
    for cfg in configs:
        print(f"[2] materializing {cfg} ({args.splits}) ...")
        records = materialize(raw_dir, cfg, args.splits, out, max_rows=args.limit)
        stats = audit_transcriptions(records, cfg)
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
    print(f"[3] audit log -> {out / 'transcription_audit.json'} ({total_rows} rows across {len(configs)} configs)")
    print("[4] NOTE: run the second-ASR QA pass before freezing; see README 'WAXAL QA pass'")
    print("[done] acquisition complete. Run scripts/freeze_checksums.py to freeze (step 5).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
