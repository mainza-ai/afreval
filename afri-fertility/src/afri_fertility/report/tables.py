"""Write study results as CSV, Parquet, and JSON."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_results(df: pd.DataFrame, outdir: str | Path) -> dict[str, Path]:
    """Write results DataFrame to CSV, Parquet, and JSON. Returns dict of paths."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    paths = {}

    csv_path = outdir / "results.csv"
    df.to_csv(csv_path, index=False)
    paths["csv"] = csv_path

    parquet_path = outdir / "results.parquet"
    df.to_parquet(parquet_path, index=False)
    paths["parquet"] = parquet_path

    json_path = outdir / "results.json"
    df.to_json(json_path, orient="records", indent=2, force_ascii=False)
    paths["json"] = json_path

    return paths


def write_scenario_costs(cost_rows: list[dict], outdir: str | Path) -> Path:
    outdir = Path(outdir) / "cost"
    outdir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(cost_rows)
    path = outdir / "scenario_costs.csv"
    df.to_csv(path, index=False)
    return path
