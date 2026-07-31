"""Generate the 6 pre-specified figures as PNG + SVG (matplotlib only, no seaborn)."""
from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    _HAS_MPL = True
except ImportError:  # pragma: no cover
    _HAS_MPL = False


def _save(fig, outdir: Path, name: str) -> None:
    for fmt in ("png", "svg"):
        fig.savefig(outdir / f"{name}.{fmt}", bbox_inches="tight", dpi=150)
    plt.close(fig)


def fig1_heatmap(df: pd.DataFrame, outdir: Path) -> None:
    """Fertility heatmap: languages × tokenizers."""
    pivot = df.pivot_table(values="fertility", index="language", columns="tokenizer", aggfunc="mean")
    if pivot.empty:
        return

    fig, ax = plt.subplots(figsize=(max(8, len(pivot.columns) * 1.5), max(6, len(pivot) * 0.5)))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    plt.colorbar(im, ax=ax, label="Fertility (tokens/word)")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=8)
    ax.set_title("Fig 1: Fertility Heatmap (languages × tokenizers)")
    ax.set_xlabel("Tokenizer")
    ax.set_ylabel("Language")
    _save(fig, outdir, "fig1_heatmap")


def fig2_premium_script(df: pd.DataFrame, outdir: Path) -> None:
    """Premium vs English, grouped and colored by script (tests H1/H2)."""
    prem_df = df[df["premium"].notna()].copy()
    if prem_df.empty:
        return

    lang_prem = (
        prem_df.groupby(["language", "script"])["premium"]
        .mean()
        .reset_index()
        .sort_values("premium", ascending=False)
    )

    scripts = lang_prem["script"].unique()
    colors = dict(zip(scripts, plt.cm.tab10.colors[:len(scripts)]))

    fig, ax = plt.subplots(figsize=(max(8, len(lang_prem) * 0.5), 6))
    bars = ax.bar(
        range(len(lang_prem)),
        lang_prem["premium"],
        color=[colors[s] for s in lang_prem["script"]],
    )
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1, label="English parity")
    ax.set_xticks(range(len(lang_prem)))
    ax.set_xticklabels(lang_prem["language"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Premium (× English)")
    ax.set_title("Fig 2: Tokenization Premium by Script")

    handles = [plt.Rectangle((0, 0), 1, 1, color=c, label=s) for s, c in colors.items()]
    handles.append(plt.Line2D([0], [0], color="black", linestyle="--", label="English parity"))
    ax.legend(handles=handles, loc="upper right", fontsize=8)
    _save(fig, outdir, "fig2_premium_script")


def fig3_cost(df: pd.DataFrame, outdir: Path) -> None:
    """Cost per 1k words: best vs worst tokenizer, USD + NGN."""
    from ..cost.model import compute_cost
    from ..cost.prices import load_default_prices
    from ..cost.fx import load_default_fx

    try:
        prices = load_default_prices()
        fx = load_default_fx()
    except Exception:
        warnings.warn("fig3: price/FX data unavailable — skipping figure")
        return

    prem_df = df[df["premium"].notna()].copy()
    if prem_df.empty:
        return

    lang_tok = prem_df.groupby(["language", "tokenizer"])["fertility"].mean().reset_index()
    eng_f = lang_tok[lang_tok["language"] == "English"]["fertility"].mean()
    if pd.isna(eng_f) or eng_f == 0:
        eng_f = 1.5  # fallback

    rows = []
    for _, row in lang_tok.iterrows():
        if row["tokenizer"] not in prices:
            continue
        try:
            cr = compute_cost(row["language"], row["tokenizer"], row["fertility"], eng_f,
                              prices=prices, fx=fx, local_currencies=["NGN"])
            rows.append({"language": row["language"], "tokenizer": row["tokenizer"],
                         "total_usd": cr.total_cost_usd, "total_ngn": cr.costs_local.get("NGN", 0)})
        except Exception:
            continue

    if not rows:
        return

    cost_df = pd.DataFrame(rows)
    best_worst = cost_df.groupby("language").agg(
        best_usd=("total_usd", "min"),
        worst_usd=("total_usd", "max"),
    ).reset_index().sort_values("worst_usd", ascending=False).head(15)

    x = range(len(best_worst))
    fig, ax = plt.subplots(figsize=(max(8, len(best_worst) * 0.6), 6))
    ax.bar([i - 0.2 for i in x], best_worst["best_usd"], 0.4, label="Best tokenizer (USD)", color="steelblue")
    ax.bar([i + 0.2 for i in x], best_worst["worst_usd"], 0.4, label="Worst tokenizer (USD)", color="tomato")
    ax.set_xticks(list(x))
    ax.set_xticklabels(best_worst["language"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Cost per 1k words (USD)")
    ax.set_title("Fig 3: Cost per 1,000 Words — Best vs Worst Tokenizer")
    ax.legend()
    _save(fig, outdir, "fig3_cost")


def fig4_context(df: pd.DataFrame, outdir: Path) -> None:
    """Context-window efficiency relative to English."""
    if "cpt" not in df.columns:
        return
    cpt_df = df.groupby("language")["cpt"].mean().reset_index()
    eng_cpt = cpt_df[cpt_df["language"] == "English"]["cpt"].values
    if len(eng_cpt) == 0:
        return
    eng_cpt = eng_cpt[0]
    cpt_df["rel_ce"] = cpt_df["cpt"] / eng_cpt
    cpt_df = cpt_df.sort_values("rel_ce", ascending=False)

    fig, ax = plt.subplots(figsize=(max(8, len(cpt_df) * 0.5), 6))
    colors = ["steelblue" if v >= 1.0 else "tomato" for v in cpt_df["rel_ce"]]
    ax.barh(cpt_df["language"], cpt_df["rel_ce"], color=colors)
    ax.axvline(1.0, color="black", linestyle="--", linewidth=1, label="English baseline")
    ax.set_xlabel("Context Efficiency (relative to English)")
    ax.set_title("Fig 4: Context-Window Efficiency vs English")
    ax.legend()
    _save(fig, outdir, "fig4_context")


def fig5_general_indomain(df: pd.DataFrame, outdir: Path) -> None:
    """General vs in-domain premium (tests H4)."""
    if "domain" not in df.columns or df["domain"].isna().all():
        return

    general = df[df["domain"].isna() | (df["domain"] == "general")]
    indomain = df[df["domain"].notna() & (df["domain"] != "general")]

    if general.empty or indomain.empty:
        return

    gen_prem = general.groupby("language")["premium"].mean().rename("general")
    ind_prem = indomain.groupby("language")["premium"].mean().rename("indomain")
    combined = pd.concat([gen_prem, ind_prem], axis=1).dropna()

    if combined.empty:
        return

    fig, ax = plt.subplots(figsize=(max(8, len(combined) * 0.7), 6))
    x = range(len(combined))
    ax.bar([i - 0.2 for i in x], combined["general"], 0.4, label="General (FLORES)", color="steelblue")
    ax.bar([i + 0.2 for i in x], combined["indomain"], 0.4, label="In-domain (health/finance/agri)", color="darkorange")
    ax.set_xticks(list(x))
    ax.set_xticklabels(combined.index, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Premium (× English)")
    ax.set_title("Fig 5: General vs In-Domain Premium (H4)")
    ax.legend()
    _save(fig, outdir, "fig5_general_indomain")


def fig6_premium_accuracy(df: pd.DataFrame, outdir: Path) -> None:
    """Premium vs downstream accuracy scatter (tests H5). Skips if no accuracy data."""
    if "accuracy" not in df.columns:
        return

    merged = df[df["premium"].notna() & df["accuracy"].notna()]
    if len(merged) < 3:
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(merged["premium"], merged["accuracy"], alpha=0.7, color="steelblue", edgecolors="white")
    for _, row in merged.iterrows():
        ax.annotate(row.get("iso639_3", ""), (row["premium"], row["accuracy"]),
                    fontsize=7, xytext=(4, 2), textcoords="offset points")
    ax.set_xlabel("Tokenization Premium (× English)")
    ax.set_ylabel("Downstream Accuracy")
    ax.set_title("Fig 6: Premium vs Downstream Accuracy (H5)")
    _save(fig, outdir, "fig6_premium_accuracy")


def generate_all(df: pd.DataFrame, outdir: str | Path) -> None:
    """Generate all 6 pre-specified figures as PNG + SVG."""
    if not _HAS_MPL:
        warnings.warn("matplotlib not installed — skipping figure generation. pip install 'afri-fertility[viz]'")
        return

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    fig1_heatmap(df, outdir)
    fig2_premium_script(df, outdir)
    fig3_cost(df, outdir)
    fig4_context(df, outdir)
    fig5_general_indomain(df, outdir)
    fig6_premium_accuracy(df, outdir)
