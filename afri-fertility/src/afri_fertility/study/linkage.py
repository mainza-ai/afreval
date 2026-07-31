"""Join per-language premiums to external accuracy table (H5 analysis)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def join_accuracy(
    results_df: pd.DataFrame,
    accuracy_csv: str | Path,
    premium_col: str = "premium",
    lang_col: str = "iso639_3",
) -> pd.DataFrame:
    """
    Join premium scores to accuracy table and compute Pearson + Spearman correlations.

    Args:
        results_df: Study results DataFrame with at least 'iso639_3' and 'premium' columns.
        accuracy_csv: Path to CSV with columns [language_code, accuracy, benchmark].
        premium_col: Column name for premium in results_df.
        lang_col: Column name for language code in results_df.

    Returns:
        DataFrame with merged premium + accuracy, and a 'correlation' dict in .attrs.
    """
    accuracy_df = pd.read_csv(accuracy_csv)

    # Aggregate premium per language (mean across tokenizers, take FLORES as primary corpus)
    premium_agg = (
        results_df[results_df["corpus"] == "flores"][[lang_col, premium_col]]
        .groupby(lang_col)[premium_col]
        .mean()
        .reset_index()
    )

    merged = premium_agg.merge(accuracy_df, left_on=lang_col, right_on="language_code", how="inner")

    if len(merged) < 3:
        merged.attrs["correlation"] = {"pearson": None, "spearman": None, "n": len(merged)}
        return merged

    from scipy import stats  # optional dep; only needed for this analysis

    pearson_r, pearson_p = stats.pearsonr(merged[premium_col], merged["accuracy"])
    spearman_r, spearman_p = stats.spearmanr(merged[premium_col], merged["accuracy"])

    merged.attrs["correlation"] = {
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_r": float(spearman_r),
        "spearman_p": float(spearman_p),
        "n": len(merged),
    }
    return merged
