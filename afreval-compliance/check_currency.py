#!/usr/bin/env python3
"""§3.6 citation-currency check. Frozen: verifies citations/africa.yaml against
the authoritative source. The mapping is the mutable artifact, not this checker.

Exit: 0 = all citations current; 1 = stale/unverified/unreachable present.
"""
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CITATIONS = HERE / "citations" / "africa.yaml"


def fetch_status(url: str, timeout: float = 15) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "afreval-compliance/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read(200_000).decode("utf-8", errors="ignore")
        return resp.status, body


def check_citation(cit: dict, offline: bool) -> dict:
    url = cit.get("url", "TBD")
    phrase = cit.get("key_phrase", "TBD")
    if offline or url == "TBD" or phrase == "TBD":
        return {"label": cit.get("label"), "url": url, "status": "unverified"}
    try:
        status, body = fetch_status(url)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as e:
        return {"label": cit.get("label"), "url": url, "status": "unreachable", "detail": str(e)[:120]}
    ok = phrase.lower() in body.lower()
    return {"label": cit.get("label"), "url": url, "status": "current" if (status == 200 and ok) else "stale"}


def main() -> int:
    ap = argparse.ArgumentParser(description="§3.6 citation-currency check")
    ap.add_argument("--offline", action="store_true", help="mark all as unverified (no network)")
    args = ap.parse_args()

    data = yaml.safe_load(CITATIONS.read_text(encoding="utf-8"))
    results: list[dict] = []
    for j in data["jurisdictions"]:
        for inst in j["instruments"]:
            for cit in inst["citations"]:
                r = check_citation(cit, args.offline)
                r["jurisdiction"] = j["jurisdiction"]
                r["instrument"] = inst["name"]
                r["binding"] = inst.get("binding", "binding")
                results.append(r)

    status_counts: dict[str, int] = {}
    for r in results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    current = status_counts.get("current", 0)
    score = current / len(results) if results else 0.0

    for r in sorted(results, key=lambda x: (x["jurisdiction"], x["instrument"])):
        print(f"  [{r['status']:10s}] {r['jurisdiction']} / {r['instrument']} — {r['label']} ({r['url'][:40]}) [{r['binding']}]")

    print(f"citation-currency: {score:.0%} ({current}/{len(results)} current)")
    ok = status_counts.get("current", 0) == len(results)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
