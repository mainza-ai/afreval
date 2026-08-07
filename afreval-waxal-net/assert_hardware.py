#!/usr/bin/env python3
"""§3.4 device-layer hardware-class assertion (gap-analysis B6).

Validates that a run's environment satisfies the TARGET hardware class from
configs/fine_tune.yaml. A claim of "beats zero-shot on low-end mobile" is
invalid if the run actually executed on faster hardware — this fails LOUD so
the Phase-4 acceptance criteria cannot be silently met on the wrong device.

Usage:
  python assert_hardware.py [--json]
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / "configs" / "fine_tune.yaml"

# Machine features we can measure portably (CPU cores + RAM). This is a coarse
# gate: it cannot detect an attached GPU, so the caller must ALSO pass
# --on-gpu if a GPU run is happening (which fails the assertion).
def machine() -> dict:
    try:
        import os
        cores = os.cpu_count() or 0
        try:
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        except ImportError:
            # Darwin sysctl fallback
            if sys.platform == "darwin":
                import subprocess
                out = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip()
                ram_gb = int(out) / (1024 ** 3)
            else:
                ram_gb = 0.0
        return {"platform": platform.system(), "cpu_cores": cores, "ram_gb": round(ram_gb, 1)}
    except Exception as e:
        return {"platform": platform.system(), "error": str(e)}


def load_hardware_class() -> dict:
    import yaml
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    hw = data["eval"]["hardware_class"]
    assert isinstance(hw, dict), "hardware_class must be a spec, not a bare label (B6)"
    return hw


def check(spec: dict, on_gpu: bool) -> tuple[bool, list[str]]:
    problems: list[str] = []
    m = machine()
    if on_gpu:
        problems.append("--on-gpu: a GPU run cannot claim the low-end-mobile target class")
    if m.get("cpu_cores") and m["cpu_cores"] > 8:
        problems.append(f"cpu_cores={m['cpu_cores']} exceeds low-end-mobile bound")
    if m.get("ram_gb") and m["ram_gb"] > 8:
        problems.append(f"ram_gb={m['ram_gb']} exceeds low-end-mobile bound (<=4GB class)")
    return (not problems, problems)


def main() -> int:
    ap = argparse.ArgumentParser(description="§3.4 device-layer hardware assertion")
    ap.add_argument("--on-gpu", action="store_true", help="declare this run uses a GPU (fails assertion)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    spec = load_hardware_class()
    ok, problems = check(spec, args.on_gpu)
    out = {
        "hardware_class": spec["name"],
        "machine": machine(),
        "ok": ok,
        "problems": problems,
        "assertion": spec.get("assertion", ""),
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"hardware_class: {spec['name']}  ok={ok}")
        for p in problems:
            print(f"  FAIL: {p}")
        print(f"  assertion: {spec.get('assertion')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
