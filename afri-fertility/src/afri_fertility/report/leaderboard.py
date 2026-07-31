"""Emit leaderboard JSON consumable by the datalens.africa frontend."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


def records_to_leaderboard(records) -> list[dict]:
    """Convert ResultRecord list to leaderboard dicts."""
    from ..cost.model import compute_cost
    from ..cost.prices import load_default_prices
    from ..cost.fx import load_default_fx

    try:
        prices = load_default_prices()
        fx = load_default_fx()
    except Exception:
        prices = None
        fx = None

    result = []
    for r in records:
        entry: dict = {
            "language": r.language,
            "iso639_3": r.iso639_3,
            "script": r.script,
            "family": r.family,
            "tokenizer": r.tokenizer,
            "fertility": round(r.fertility, 4),
            "premium": round(r.premium, 4) if (r.premium is not None and not (isinstance(r.premium, float) and math.isnan(r.premium))) else None,
            "cpt": round(r.cpt, 4),
            "cost_per_1k_usd": None,
            "cost_per_1k_ngn": None,
            "cost_per_1k_zar": None,
        }
        if prices and fx and r.tokenizer in prices:
            try:
                cost = compute_cost(
                    language=r.iso639_3,
                    tokenizer_id=r.tokenizer,
                    fertility=r.fertility,
                    baseline_fertility=r.fertility,
                    prices=prices,
                    fx=fx,
                    reference_words=1000,
                    local_currencies=["NGN", "ZAR"],
                )
                entry["cost_per_1k_usd"] = round(cost.total_cost_usd, 6)
                entry["cost_per_1k_ngn"] = round(cost.costs_local.get("NGN", 0), 4)
                entry["cost_per_1k_zar"] = round(cost.costs_local.get("ZAR", 4), 4)
            except Exception:
                pass
        result.append(entry)
    return result


def emit_leaderboard(records, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = records_to_leaderboard(records)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return out_path
