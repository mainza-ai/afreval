#!/usr/bin/env python3
"""Finalize WAXAL QA pass 2: aggregate results, compute the drop list, write a
human-reviewable report. The human reviews qa2_review.md and approves drops;
only then does freeze_checksums.py close the Phase 0 gate.

Flagging (adaptive per language, matching qa_waxal_tuned):
  wer >= 1.0 OR decode_failed OR wer > max(0.40, median + 4*1.4826*MAD)
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

WAXAL = HARNESS_ROOT / "data" / "waxal"
ADAPTIVE_K = 4.0
FLOOR = 0.40


def flagged_rows(config: str) -> list[dict]:
    p = WAXAL / f"{config}_qa2.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    wers = [r["wer"] for r in rows]
    med = statistics.median(wers) if wers else 0.0
    mad = statistics.median([abs(w - med) for w in wers]) if wers else 0.0
    high = max(FLOOR, med + ADAPTIVE_K * (1.4826 * mad))
    return [
        r for r in rows
        if r["wer"] >= 1.0 or r["decode_failed"] or r["wer"] > high
    ], med, high, len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="WAXAL QA finalization (drop list + review)")
    ap.add_argument("--apply", action="store_true", help="write filtered manifests (after human approval)")
    args = ap.parse_args()

    configs = sorted(p.name.removesuffix("_qa2.jsonl") for p in WAXAL.glob("*_qa2.jsonl"))
    drops: dict[str, list[str]] = {}
    lines = ["# WAXAL QA review — drop list (human review required)", ""]
    total_rows = total_flags = 0
    for cfg in configs:
        flagged, med, high, n = flagged_rows(cfg)
        total_rows += n
        total_flags += len(flagged)
        drops[cfg] = [f["id"] for f in flagged]
        lines.append(f"## {cfg}  ({len(flagged)}/{n} flagged; median WER {med:.3f}; adaptive high {high:.3f})")
        for f in flagged:
            snippet = (f.get("hypothesis") or "")[:60].replace("\n", " ")
            lines.append(f"- `{f['id']}` wer={f['wer']:.3f} {'decode_failed' if f['decode_failed'] else ''} | {snippet}")
        lines.append("")

    review = WAXAL / "qa2_review.md"
    review.write_text("\n".join(lines))
    (WAXAL / "qa2_drops.json").write_text(json.dumps(drops, indent=2))
    print(f"review -> {review}")
    print(f"drops  -> {WAXAL / 'qa2_drops.json'}")
    print(f"total rows={total_rows} flagged={total_flags} across {len(configs)} configs")

    if args.apply:
        for cfg, ids in drops.items():
            man = WAXAL / f"{cfg}.jsonl"
            if not man.exists():
                continue
            drop_set = set(ids)
            rows = [json.loads(l) for l in man.read_text(encoding="utf-8").splitlines() if l.strip()]
            kept = [r for r in rows if r["id"] not in drop_set]
            dst = WAXAL / f"{cfg}_filtered.jsonl"
            with open(dst, "w", encoding="utf-8") as f:
                for r in kept:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"filtered {cfg}: {len(rows)} -> {len(kept)} (wrote {dst.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
