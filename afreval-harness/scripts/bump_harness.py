#!/usr/bin/env python3
"""Harness bump procedure — the documented, human-approved way to change a pin.

Per Phase 0 acceptance and the risk register, an unplanned silent bump is the
exact kind of drift that invalidates historical Context Scores. This script:
  1. Requires an explicit reason and a human approver.
  2. Rewrites the requested pin file's pinned_version / vendored_commit / date.
  3. Sets status back to 'pending-freeze' and clears checksums (re-freeze after).
  4. Appends the change to PROVENANCE.md (append-only).
It does NOT run freeze_checksums — that is a separate, deliberate step.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import yaml

HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_ROOT))

from harness.pins import PIN_DIR  # noqa: E402

PROVENANCE = HARNESS_ROOT / "PROVENANCE.md"

PIN_META_FIELDS = {
    "afri_fertility.yaml": ("pinned_version", "vendored_commit"),
    "afrobench_lite.yaml": ("pinned_version", "vendored_commit", "harness_submodule"),
    "waxal.yaml": ("pinned_version", "hf_revision"),
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Bump a harness pin (human-approved, provenance-logged)")
    ap.add_argument("--pin", choices=list(PIN_META_FIELDS), required=True)
    ap.add_argument("--to", required=True, help="new pinned version / commit / revision")
    ap.add_argument("--reason", required=True, help="why this bump is justified (mandatory)")
    ap.add_argument("--approved-by", required=True, help="human approver name (mandatory)")
    ap.add_argument("--vendor-commit", help="new vendored commit hash (where applicable)")
    args = ap.parse_args()

    path = PIN_DIR / args.pin
    pin = yaml.safe_load(path.read_text(encoding="utf-8"))
    fields = PIN_META_FIELDS[args.pin]

    old = {f: pin.get(f) for f in fields}
    pin[fields[0]] = args.to
    if args.vendor_commit and "vendored_commit" in fields:
        pin["vendored_commit"] = args.vendor_commit
    pin["pinned_date"] = str(date.today())
    pin["status"] = "pending-freeze"
    pin["checksums"] = []
    path.write_text(yaml.safe_dump(pin, sort_keys=False), encoding="utf-8")

    entry = (
        f"## {date.today()} bump | {args.pin}\n"
        f"- from: {old}\n"
        f"- to: {args.to}"
        f"{f' (vendor commit {args.vendor_commit})' if args.vendor_commit else ''}\n"
        f"- reason: {args.reason}\n"
        f"- approved-by: {args.approved_by}\n"
        f"- status: pending-freeze (run scripts/freeze_checksums.py --pin {args.pin})\n"
    )
    with open(PROVENANCE, "a", encoding="utf-8") as f:
        f.write("\n" + entry)

    print(f"[bumped] {args.pin} -> {args.to} (status: pending-freeze)")
    print(f"provenance appended to PROVENANCE.md; re-freeze with:")
    print(f"  python scripts/freeze_checksums.py --pin {args.pin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
