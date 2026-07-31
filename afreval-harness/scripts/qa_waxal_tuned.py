#!/usr/bin/env python3
"""WAXAL §2.1.1 step 3 — QA edit-distance pass, WAXAL-tuned ASRs.

Uses corpus-appropriate models (general zero-shot ASRs fail on WAXAL's
spontaneous natural-environment speech — see pin qa_findings):
  - Ethio-ASR  (badrex/Ethio-ASR-multilingual-600M, CTC)  -> amh, tir, orm, sid, wal
  - Sunbird    (Sunbird/asr-whisper-51-african-languages) -> ach, aka, dag, dga, ewe,
               ful, kpo, lin, lug, mlg, nyn, sna, sog(xog), amh, ...
mas_asr has no coverage in either model (deferred; needs human QA).

Run with a torch-enabled Python (the harness venv does not have torch):
  /path/to/torch-venv/bin/python scripts/qa_waxal_tuned.py --out data/waxal
Resumable: per-config state files; an interrupted run continues where it stopped.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from harness.waxal_eval import cer, wer  # noqa: E402

ETHIO_ASR = "badrex/Ethio-ASR-multilingual-600M"
SUNBIRD = "Sunbird/asr-whisper-51-african-languages"

# config -> (model, whisper language token key)
ROUTING: dict[str, tuple[str, str]] = {
    "amh_asr": (ETHIO_ASR, "amh"), "tir_asr": (ETHIO_ASR, "tir"),
    "orm_asr": (ETHIO_ASR, "orm"), "sid_asr": (ETHIO_ASR, "sid"),
    "wal_asr": (ETHIO_ASR, "wal"),
    "ach_asr": (SUNBIRD, "ach"), "aka_asr": (SUNBIRD, "aka"),
    "dag_asr": (SUNBIRD, "dag"), "dga_asr": (SUNBIRD, "dga"),
    "ewe_asr": (SUNBIRD, "ewe"), "ful_asr": (SUNBIRD, "ful"),
    "kpo_asr": (SUNBIRD, "kpo"), "lin_asr": (SUNBIRD, "lin"),
    "lug_asr": (SUNBIRD, "lug"), "mlg_asr": (SUNBIRD, "mlg"),
    "nyn_asr": (SUNBIRD, "nyn"), "sna_asr": (SUNBIRD, "sna"),
    "sog_asr": (SUNBIRD, "xog"),   # Lusoga = Soga
}

SUNBIRD_TOKENS = {
    "eng": 50259, "fra": 50265, "swa": 50318, "sna": 50324, "yor": 50325, "som": 50326,
    "afr": 50327, "amh": 50334, "mlg": 50349, "lin": 50353, "hau": 50354,
    "ach": 50357, "aka": 50356, "bam": 50355, "bem": 50352, "ber": 50351,
    "cgg": 50350, "dag": 50348, "dga": 50347, "ewe": 50346, "ful": 50345,
    "ibo": 50344, "kab": 50343, "kau": 50342, "kik": 50341, "kin": 50340,
    "kln": 50339, "koo": 50338, "kpo": 50337, "led": 50336, "lgg": 50335,
    "lth": 50333, "lug": 50332, "luo": 50331, "luy": 50330, "myx": 50329,
    "nbl": 50328, "nya": 50323, "nyn": 50322, "orm": 50321, "pcm": 50320,
    "ruc": 50319, "rwm": 50317, "sot": 50316, "teo": 50315, "tsn": 50314,
    "ttj": 50313, "wol": 50312, "xho": 50311, "xog": 50310, "zul": 50309,
}


def load_model(model_id: str, torch):
    from transformers import (
        AutoModelForCTC, AutoProcessor,
        WhisperForConditionalGeneration, WhisperProcessor,
    )
    if model_id == ETHIO_ASR:
        proc = AutoProcessor.from_pretrained(model_id)
        model = AutoModelForCTC.from_pretrained(model_id)
        model.eval()
        return ("ctc", model, proc)
    proc = WhisperProcessor.from_pretrained(model_id)
    model = WhisperForConditionalGeneration.from_pretrained(model_id)
    model.eval()
    return ("whisper", model, proc)


def build_transcriber(kind, model, proc, lang, torch):
    if kind == "ctc":
        def transcribe_batch(paths):
            import soundfile as sf
            import torchaudio.functional as taF
            audios, lens = [], []
            for p in paths:
                a, sr = sf.read(p, dtype="float32")
                if a.ndim > 1:
                    a = a.mean(axis=1)
                if a.size == 0:
                    audios.append(None); lens.append(0); continue
                if sr != 16000:
                    a = taF.resample(torch.from_numpy(a), sr, 16000).numpy()
                audios.append(a); lens.append(len(a))
            outs = []
            # process non-empty sequentially (variable-length padding wastes GPU/CPU)
            for a in audios:
                if a is None:
                    outs.append(""); continue
                inputs = proc(a, sampling_rate=16000, return_tensors="pt")
                with torch.no_grad():
                    logits = model(**inputs).logits
                pred = torch.argmax(logits, dim=-1)
                text = proc.batch_decode(pred)[0]
                outs.append(text.strip())
            return outs
        return transcribe_batch

    tok = SUNBIRD_TOKENS[lang]
    forced = [(1, tok), (2, proc.tokenizer.convert_tokens_to_ids("<|transcribe|>")),
              (3, proc.tokenizer.convert_tokens_to_ids("<|notimestamps|>"))]

    def transcribe_batch(paths):
        import soundfile as sf
        import torchaudio.functional as taF
        outs = []
        for p in paths:
            a, sr = sf.read(p, dtype="float32")
            if a.ndim > 1:
                a = a.mean(axis=1)
            if a.size == 0:
                outs.append(""); continue
            if sr != 16000:
                a = taF.resample(torch.from_numpy(a), sr, 16000).numpy()
            feats = proc(a, sampling_rate=16000, do_normalize=True, return_tensors="pt").input_features
            with torch.no_grad():
                ids = model.generate(feats, forced_decoder_ids=forced,
                                     num_beams=1, do_sample=False)
            outs.append(proc.decode(ids[0], skip_special_tokens=True,
                                    clean_up_tokenization_spaces=False).strip())
        return outs
    return transcribe_batch


def main() -> int:
    ap = argparse.ArgumentParser(description="WAXAL QA pass 2 with WAXAL-tuned ASRs")
    ap.add_argument("--out", default=str(HARNESS_ROOT / "data/waxal"))
    ap.add_argument("--configs", nargs="*", help="subset of configs (default: all routed)")
    ap.add_argument("--threads", type=int, default=8, help="torch threads")
    ap.add_argument("--batch", type=int, default=4, help="clips per inference call")
    ap.add_argument("--limit", type=int, help="cap clips per config (smoke only)")
    ap.add_argument("--no-resume", action="store_true")
    args = ap.parse_args()

    import torch
    torch.set_num_threads(args.threads)

    out = Path(args.out)
    configs = [c for c in ROUTING if (out / f"{c}.jsonl").exists()]
    if args.configs:
        configs = [c for c in configs if c in args.configs]
    if not configs:
        print("no routed configs found under", out)
        return 1

    print(f"[qa2] threads={args.threads} batch={args.batch} configs={len(configs)}")
    print(f"[qa2] configs: {', '.join(configs)}")

    # load models lazily per family, reuse across configs
    import torch as _torch
    _models: dict[str, tuple] = {}

    for cfg in configs:
        model_id, lang = ROUTING[cfg]
        if model_id not in _models:
            print(f"[qa2] loading {model_id} ...")
            _models[model_id] = load_model(model_id, _torch)
        kind, model, proc = _models[model_id]
        transcribe = build_transcriber(kind, model, proc, lang, _torch)

        rows = [json.loads(l) for l in (out / f"{cfg}.jsonl").read_text().splitlines()]
        state_path = out / f"{cfg}_qa2_state.json"
        qa_path = out / f"{cfg}_qa2.jsonl"
        done = 0
        if not args.no_resume and state_path.exists():
            done = int(json.loads(state_path.read_text()).get("done", 0))
        print(f"[qa2] {cfg} ({lang}) {len(rows)} clips, resume at {done}")

        f = open(qa_path, "a" if done else "w", encoding="utf-8")
        batch = []
        for i, r in enumerate(rows[done:], start=done):
            batch.append(r)
            if len(batch) >= args.batch:
                hyps = transcribe([str(out / r["audio_path"]) for r in batch])
                for rr, h in zip(batch, hyps):
                    f.write(json.dumps({
                        "id": rr["id"], "split": rr["split"], "language": rr["language"],
                        "shipped": rr["transcription"], "hypothesis": h,
                        "wer": round(wer(rr["transcription"], h), 6),
                        "cer": round(cer(rr["transcription"], h), 6),
                        "decode_failed": not h,
                    }, ensure_ascii=False) + "\n")
                    done += 1
                batch = []
                f.flush()
                state_path.write_text(json.dumps({"done": done}))
                if args.limit and done >= args.limit:
                    break
        if batch and not (args.limit and done >= args.limit):
            hyps = transcribe([str(out / r["audio_path"]) for r in batch])
            for rr, h in zip(batch, hyps):
                f.write(json.dumps({
                    "id": rr["id"], "split": rr["split"], "language": rr["language"],
                    "shipped": rr["transcription"], "hypothesis": h,
                    "wer": round(wer(rr["transcription"], h), 6),
                    "cer": round(cer(rr["transcription"], h), 6),
                    "decode_failed": not h,
                }, ensure_ascii=False) + "\n")
                done += 1
            f.flush()
            state_path.write_text(json.dumps({"done": done}))
        f.close()
        print(f"[qa2] done {cfg}: {done}/{len(rows)}")

    # summary
    summary = {"configs": [], "total_rows": 0, "total_flagged": 0}
    for cfg in configs:
        qa_path = out / f"{cfg}_qa2.jsonl"
        if not qa_path.exists():
            continue
        rows = [json.loads(l) for l in qa_path.read_text().splitlines() if l.strip()]
        wers = [r["wer"] for r in rows]
        med = statistics.median(wers) if wers else 0.0
        mad = statistics.median([abs(w - med) for w in wers]) if wers else 0.0
        high = max(0.40, med + 4.0 * (1.4826 * mad))
        flagged = [r for r in rows if r["wer"] >= 1.0 or r["wer"] > high or r["decode_failed"]]
        summary["configs"].append({
            "config": cfg, "rows": len(rows), "median_wer": round(med, 4),
            "adaptive_high": round(high, 4), "flagged": len(flagged),
            "flagged_ids": [r["id"] for r in flagged][:200],
        })
        summary["total_rows"] += len(rows)
        summary["total_flagged"] += len(flagged)
    (out / "qa2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[qa2] summary -> data/waxal/qa2_summary.json ({summary['total_rows']} rows, {summary['total_flagged']} flagged)")
    for c in summary["configs"]:
        print(f"    {c['config']:12s} rows={c['rows']:6d} med_wer={c['median_wer']:.3f} "
              f"adaptive_high={c['adaptive_high']:.3f} flagged={c['flagged']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
