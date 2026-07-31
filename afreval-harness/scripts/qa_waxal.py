#!/usr/bin/env python3
"""WAXAL §2.1.1 step 3 — QA edit-distance pass (the REAL filter).

Re-transcribes the acquired eval corpus with a second ASR (faster-whisper /
CTranslate2) and computes per-clip WER/CER against the shipped transcriptions
(harness.waxal_eval). Flags rows for exclusion before the harness is frozen.

Adaptive thresholding is essential: ~half of the WAXAL languages are NOT in
Whisper's ~100-language set (ach, dag, dga, kpo, mas, nyn, sid, sog, wal, ewe,
lug, ...). A global WER threshold would flag nearly every clip in those
languages as 'high-divergence' when the divergence is really Whisper's, not
the dataset's. So we flag per language:
  - WER >= 1.0                      (completely different -> likely misaligned)
  - OR WER > max(global_threshold, language_median_WER + k*MAD)   (outlier)

Design:
  - One worker process per config; the model is loaded once per process and
    reused across the config's clips (batch_size batches segments per clip).
  - Checkpointed: results are appended per batch and a state file records how
    many clips are done, so an interrupted run resumes mid-config.
  - cpu_threads is divided across workers to avoid oversubscription.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from harness.waxal_eval import cer, wer  # noqa: E402

DEFAULT_MODEL = "large-v3-turbo"
GLOBAL_WER_THRESHOLD = 0.40
MAD_K = 4.0

# WAXAL ISO 639-3 -> Whisper language code (Whisper's ~100-language set).
# Languages absent from this map are transcribed with autodetect; their QA
# verdicts rely on the adaptive per-language threshold, not a global one.
WHISPER_LANGS: dict[str, str] = {
    "amh": "am", "aka": "ak", "ful": "ff", "lin": "ln", "lug": "lg",
    "mlg": "mg", "orm": "om", "sna": "sn", "tir": "ti",
}


def load_manifest(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def transcribe_clips(model, clips: list[tuple[str, str]], language: str | None,
                     batch_size: int) -> list[str]:
    """Transcribe a batch of (audio_path, ...) clips; returns hypotheses."""
    hypotheses: list[str] = []
    for audio_path, _shipped in clips:
        try:
            segments, _info = model.transcribe(
                audio_path,
                language=language,
                beam_size=1,
                batch_size=batch_size,
                vad_filter=True,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
            )
            text = "".join(s.text for s in segments).strip()
        except Exception:  # noqa: BLE001 - per-clip decode failure
            text = ""
        hypotheses.append(text)
    return hypotheses


def worker(config: str, out_dir: Path, manifest_path: Path, audio_root: Path,
           model_name: str, cpu_threads: int, batch_size: int, resume: bool) -> dict:
    """Process one config: transcribe, score, write {config}_qa.jsonl.

    Returns per-language summary stats. Runs in its own process (model reused).
    """
    from faster_whisper import WhisperModel

    rows = load_manifest(manifest_path)
    lang = config.removesuffix("_asr")
    language = WHISPER_LANGS.get(lang)
    state_path = out_dir / f"{config}_state.json"
    qa_path = out_dir / f"{config}_qa.jsonl"

    done = 0
    if resume and state_path.exists():
        done = int(json.loads(state_path.read_text()).get("done", 0))

    model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=cpu_threads)
    out_f = open(qa_path, "a" if done else "w", encoding="utf-8")

    def score_and_write(clip_rows, hypotheses):
        nonlocal done
        for row, hyp in zip(clip_rows, hypotheses):
            shipped = row.get("transcription", "")
            w = wer(shipped, hyp)
            c = cer(shipped, hyp)
            out_f.write(json.dumps({
                "id": row["id"], "split": row["split"], "language": row["language"],
                "shipped": shipped, "hypothesis": hyp, "wer": round(w, 6),
                "cer": round(c, 6), "decode_failed": not hyp,
            }, ensure_ascii=False) + "\n")
            done += 1

    batch: list[dict] = []
    batch_paths: list[tuple[str, str]] = []
    for row in rows[done:]:
        audio_path = str(audio_root / row["audio_path"].removeprefix("audio/"))
        batch.append(row)
        batch_paths.append((audio_path, row.get("transcription", "")))
        if len(batch) >= batch_size:
            score_and_write(batch, transcribe_clips(model, batch_paths, language, batch_size))
            batch, batch_paths = [], []
            out_f.flush()
            state_path.write_text(json.dumps({"done": done}))
    if batch:
        score_and_write(batch, transcribe_clips(model, batch_paths, language, batch_size))
        out_f.flush()
        state_path.write_text(json.dumps({"done": done}))
    out_f.close()

    return {"config": config, "language": lang, "rows": len(rows), "done": done}


def summarize(out_dir: Path, configs: list[str], threshold: float, k: float) -> dict:
    """Aggregate per-config QA, apply adaptive thresholds, recommend drops."""
    summary: dict = {"configs": [], "total_flagged": 0, "total_rows": 0}
    for cfg in configs:
        qa_path = out_dir / f"{cfg}_qa.jsonl"
        if not qa_path.exists():
            continue
        rows = [json.loads(l) for l in qa_path.read_text().splitlines() if l.strip()]
        wers = [r["wer"] for r in rows]
        med = statistics.median(wers) if wers else 0.0
        mad = statistics.median([abs(w - med) for w in wers]) if wers else 0.0
        high = max(threshold, med + k * (1.4826 * mad))
        flagged = [r for r in rows if r["wer"] >= 1.0 or r["wer"] > high or r["decode_failed"]]
        summary["configs"].append({
            "config": cfg, "rows": len(rows), "median_wer": round(med, 4),
            "adaptive_high": round(high, 4), "flagged": len(flagged),
            "flagged_ids": [r["id"] for r in flagged][:200],
        })
        summary["total_rows"] += len(rows)
        summary["total_flagged"] += len(flagged)
    summary["global_threshold"] = threshold
    summary["mad_k"] = k
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description="WAXAL QA edit-distance pass (§2.1.1 step 3)")
    ap.add_argument("--out", default=str(HARNESS_ROOT / "data/waxal"), help="corpus dir (manifests + audio/)")
    ap.add_argument("--configs", nargs="*", help="subset of configs to QA (default: all 19)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--workers", type=int, default=8, help="parallel worker processes")
    ap.add_argument("--cpu-threads", type=int, default=2, help="CTranslate2 threads per worker (16 cores / workers)")
    ap.add_argument("--batch", type=int, default=16, help="segments per faster-whisper batch")
    ap.add_argument("--threshold", type=float, default=GLOBAL_WER_THRESHOLD)
    ap.add_argument("--mad-k", type=float, default=MAD_K)
    ap.add_argument("--no-resume", action="store_true", help="restart configs already partially done")
    args = ap.parse_args()

    out = Path(args.out)
    manifests = sorted(out.glob("*_asr.jsonl"))
    configs = [m.name.removesuffix(".jsonl") for m in manifests]
    if args.configs:
        configs = [c for c in configs if c in args.configs]

    print(f"[qa] model={args.model} workers={args.workers} cpu_threads={args.cpu_threads} "
          f"batch={args.batch} configs={len(configs)}")
    print(f"[qa] ~{sum(1 for l in (out/f'{c}.jsonl').read_text().splitlines() for c in configs)} clips "
          f"| language hints: {len(WHISPER_LANGS)}/19 langs in Whisper (others use autodetect + adaptive threshold)")

    import concurrent.futures

    results: list[dict] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {
            ex.submit(worker, c, out, out / f"{c}.jsonl", out / "audio",
                      args.model, args.cpu_threads, args.batch, not args.no_resume): c
            for c in configs
        }
        for fut in concurrent.futures.as_completed(futs):
            cfg = futs[fut]
            try:
                r = fut.result()
                results.append(r)
                print(f"[qa] done {cfg}: {r['done']}/{r['rows']} clips")
            except Exception as exc:  # noqa: BLE001
                print(f"[qa] FAILED {cfg}: {exc}", file=sys.stderr)

    summary = summarize(out, configs, args.threshold, args.mad_k)
    (out / "qa_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[qa] summary -> data/waxal/qa_summary.json")
    print(f"[qa] total_rows={summary['total_rows']} flagged={summary['total_flagged']}")
    for c in summary["configs"]:
        print(f"    {c['config']:12s} rows={c['rows']:6d} med_wer={c['median_wer']:.3f} "
              f"adaptive_high={c['adaptive_high']:.3f} flagged={c['flagged']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
