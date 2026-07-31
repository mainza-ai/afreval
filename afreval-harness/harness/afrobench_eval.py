"""AfroBench-LITE textual pipeline (§2.2, §3.2 harness).

The frozen harness for the Linguistic Fidelity (textual) component of the
Context Score. This module pins the LITE task set and language list and
validates them against the vendored AfroBench / lm-evaluation-harness
artifacts. It does NOT run inference — certification runs are a deterministic
invocation of the pinned lm-eval group `afrobench_lite` (never agent-optimized,
per §3.2.1).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .pins import PIN_DIR

HARNESS_ROOT = Path(__file__).resolve().parents[1]
VENDORED_AFROBENCH = HARNESS_ROOT.parent / "AfroBench"
LITE_GROUP_FILE = (
    VENDORED_AFROBENCH
    / "lm-evaluation-harness/lm_eval/tasks/afrobench/afrobench-lite.yaml"
)


class LITEPinError(ValueError):
    pass


def load_lite_pin() -> dict[str, Any]:
    return yaml.safe_load((PIN_DIR / "afrobench_lite.yaml").read_text(encoding="utf-8"))


def validate_vendored_lite(pin: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cross-check the pin against the vendored AfroBench artifacts.

    Raises LITEPinError if the vendored group file or its task list diverges
    from the pin — the first line of defense against silent upstream drift.
    """
    pin = pin or load_lite_pin()
    if not LITE_GROUP_FILE.exists():
        raise LITEPinError(f"vendored lite group file missing: {LITE_GROUP_FILE}")
    group = yaml.safe_load(LITE_GROUP_FILE.read_text(encoding="utf-8"))
    vendored_tasks = group.get("task", [])
    pinned_tasks = pin["task_set"]
    if set(vendored_tasks) != set(pinned_tasks):
        raise LITEPinError(
            f"vendored afrobench_lite task list diverges from pin: "
            f"only-in-vendored={sorted(set(vendored_tasks) - set(pinned_tasks))} "
            f"only-in-pin={sorted(set(pinned_tasks) - set(vendored_tasks))}"
        )
    return {"group": group.get("group"), "tasks": vendored_tasks, "pinned_languages": pin["languages"]}


def pipeline_spec() -> dict[str, str]:
    """The deterministic certification invocation spec (auditable, repeatable)."""
    pin = load_lite_pin()
    return {
        "harness_group": pin["harness_group"],
        "lm_eval_harness_commit": pin["harness_submodule"],
        "vendor_commit": pin["vendored_commit"],
        "languages": ",".join(pin["languages"]),
        "metrics": ",".join(pin["metrics"]),
    }
