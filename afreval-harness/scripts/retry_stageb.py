#!/usr/bin/env python3
"""Container/cron-friendly Stage B retry — resumes the WAXAL train-split pull.

Stage B (labeled train) is blocked on upstream HF Xet 404s at the pinned
revision. snapshot_download is resumable (cached shards persist), so this
wrapper polls and resumes the moment HF recovers — safe to run from cron or
as a Docker one-shot that retries.

Usage:
  python retry_stageb.py [--max-attempts N] [--wait-secs S] [--once]

  --once      do a single attempt and exit (for cron/Docker scheduled runs)
  (default)   retry in a loop until success or --max-attempts
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
ACQUIRE = HARNESS / "scripts" / "acquire_waxal.py"


def hf_ready() -> bool:
    """True when the pinned train blob is reachable (upstream recovered)."""
    import urllib.request

    url = ("https://huggingface.co/datasets/google/WaxalNLP/resolve/"
           "e0a62aaebc61bd5bb8cac17a08d1b42c65551dd2/data/ASR/dag/dag-train-00000.parquet")
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False


def run_acquire() -> int:
    return subprocess.run(
        [sys.executable, str(ACQUIRE), "--splits", "train", "validation", "test"],
        cwd=HARNESS,
    ).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage B retry (resumable)")
    ap.add_argument("--max-attempts", type=int, default=0, help="0 = until success")
    ap.add_argument("--wait-secs", type=int, default=600)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    attempts = 0
    while True:
        attempts += 1
        if not hf_ready():
            print(f"[{attempts}] upstream HF Xet still 404 — waiting {args.wait_secs}s", flush=True)
            if args.once:
                return 0  # scheduled run: nothing to do yet, not an error
            if args.max_attempts and attempts >= args.max_attempts:
                return 0
            time.sleep(args.wait_secs)
            continue
        print(f"[{attempts}] upstream recovered — resuming Stage B pull", flush=True)
        return run_acquire()


if __name__ == "__main__":
    raise SystemExit(main())
