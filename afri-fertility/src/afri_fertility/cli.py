"""CLI: afri-fertility command using Typer."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="afri-fertility",
    help="Measure the tokenization tax on African languages.",
    no_args_is_help=True,
)
console = Console()


# ---------- Global options ----------

def _setup_globals(
    cache_dir: Optional[str] = None,
    hf_token: Optional[str] = None,
    log_level: str = "WARNING",
) -> None:
    import logging
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.WARNING))

    if cache_dir:
        import os
        os.environ["AFRI_FERTILITY_CACHE_DIR"] = cache_dir

    if hf_token:
        import os
        os.environ["HF_TOKEN"] = hf_token


def _register_hf(hf_token: Optional[str] = None, local_only: bool = False,
                 model_ids: Optional[list] = None) -> None:
    """Lazily register HF tokenizer adapters.

    model_ids: only register these specific ids (use for measure/cost to avoid
               downloading every model in the registry).
    local_only: cache-only, no network — for informational commands.
    """
    from afri_fertility.tokenizers.hf_adapter import (
        register_all_hf, register_hf_by_ids, _get_hf_token,
    )
    token = hf_token or _get_hf_token()
    if model_ids is not None:
        register_hf_by_ids(model_ids, hf_token=token, force_local=local_only)
    else:
        register_all_hf(hf_token=token, force_local=local_only)


def _register_api() -> None:
    """Register Claude and Gemini API adapters if the [api] extra is installed."""
    import importlib.util

    def _spec(name: str) -> bool:
        try:
            return importlib.util.find_spec(name) is not None
        except (ModuleNotFoundError, ValueError):
            return False

    if _spec("anthropic") or _spec("google.generativeai"):
        from afri_fertility.tokenizers.api_adapter import register_api_adapters
        register_api_adapters()


# ---------- measure ----------

@app.command()
def measure(
    text: str = typer.Option(..., "--text", "-t", help="Text to measure."),
    lang: Optional[str] = typer.Option(None, "--lang", help="ISO 639-3 language code (informational)."),
    models: str = typer.Option("openai/o200k_base", "--models", help="Comma-separated tokenizer ids."),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
    hf_token: Optional[str] = typer.Option(None, "--hf-token", envvar="HF_TOKEN"),
    cache_dir: Optional[str] = typer.Option(None, "--cache-dir"),
    log_level: str = typer.Option("WARNING", "--log-level"),
) -> None:
    """Measure fertility and token count for input text across tokenizers."""
    import os, logging
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    logging.getLogger("transformers").setLevel(logging.ERROR)
    _setup_globals(cache_dir=cache_dir, hf_token=hf_token, log_level=log_level)
    tok_ids = [t.strip() for t in models.split(",")]
    _register_hf(hf_token, model_ids=tok_ids)
    _register_api()

    from afri_fertility import measure_text
    from afri_fertility.tokenizers.base import UnavailableAdapter, TokenizerUnavailableError
    from afri_fertility.tokenizers import REGISTRY

    if json_output:
        import json
        results = []
        for tok_id in tok_ids:
            try:
                m = measure_text(text, tokenizer=tok_id)
                results.append({
                    "tokenizer": tok_id, "tokens": m.tokens, "words": m.words,
                    "fertility": m.fertility, "cpt": m.cpt, "bpt": m.bpt,
                })
            except Exception as e:
                results.append({"tokenizer": tok_id, "error": str(e)})
        typer.echo(json.dumps(results, indent=2))
        return

    table = Table(title=f"measure: {text[:60]!r}" + (f" [{lang}]" if lang else ""))
    table.add_column("Tokenizer", style="cyan")
    table.add_column("Tokens", justify="right")
    table.add_column("Words", justify="right")
    table.add_column("Fertility", justify="right")
    table.add_column("CPT", justify="right")
    table.add_column("BPT", justify="right")

    for tok_id in tok_ids:
        try:
            m = measure_text(text, tokenizer=tok_id)
            table.add_row(tok_id, str(m.tokens), str(m.words),
                          f"{m.fertility:.3f}", f"{m.cpt:.2f}", f"{m.bpt:.2f}")
        except Exception as e:
            table.add_row(tok_id, "[red]error[/red]", "-", "-", "-", "-")
            console.print(f"[yellow]  {tok_id}: {e}[/yellow]")

    console.print(table)


# ---------- cost ----------

@app.command()
def cost(
    text: str = typer.Option(..., "--text", "-t"),
    lang: str = typer.Option("eng", "--lang"),
    models: str = typer.Option("openai/o200k_base", "--models"),
    out_in_ratio: float = typer.Option(1.0, "--out-in-ratio"),
    currencies: str = typer.Option("NGN,ZAR,KES", "--currencies"),
    json_output: bool = typer.Option(False, "--json"),
    hf_token: Optional[str] = typer.Option(None, "--hf-token", envvar="HF_TOKEN"),
    cache_dir: Optional[str] = typer.Option(None, "--cache-dir"),
) -> None:
    """Compute cost for input text per tokenizer (FR-26 widget backend)."""
    _setup_globals(cache_dir=cache_dir, hf_token=hf_token)
    tok_ids = [t.strip() for t in models.split(",")]
    _register_hf(hf_token, model_ids=tok_ids)

    from afri_fertility import measure_text
    from afri_fertility.cost.prices import load_default_prices
    from afri_fertility.cost.fx import load_default_fx
    from afri_fertility.cost.model import compute_cost
    local_currencies = [c.strip() for c in currencies.split(",")]

    try:
        prices = load_default_prices()
        fx = load_default_fx()
    except Exception as e:
        console.print(f"[red]Cannot load prices/FX: {e}[/red]")
        raise typer.Exit(1)

    if json_output:
        import json
        results = []
        for tok_id in tok_ids:
            try:
                m = measure_text(text, tokenizer=tok_id)
                if tok_id not in prices:
                    continue
                cr = compute_cost(lang, tok_id, m.fertility, m.fertility, prices, fx,
                                  out_in_ratio=out_in_ratio, local_currencies=local_currencies)
                results.append({
                    "tokenizer": tok_id, "fertility": cr.fertility,
                    "n_tokens": cr.n_tokens, "total_cost_usd": cr.total_cost_usd,
                    "costs_local": cr.costs_local,
                })
            except Exception as e:
                results.append({"tokenizer": tok_id, "error": str(e)})
        typer.echo(json.dumps(results, indent=2))
        return

    table = Table(title=f"cost [{lang}]: {text[:50]!r}")
    table.add_column("Tokenizer", style="cyan")
    table.add_column("Fertility", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("USD/1k words", justify="right")
    for cur in local_currencies:
        table.add_column(f"{cur}/1k words", justify="right")

    for tok_id in tok_ids:
        try:
            m = measure_text(text, tokenizer=tok_id)
            if tok_id not in prices:
                table.add_row(tok_id, f"{m.fertility:.3f}", str(m.n_tokens if hasattr(m, 'n_tokens') else m.tokens), "[dim]no price[/dim]", *["[dim]-[/dim]"] * len(local_currencies))
                continue
            cr = compute_cost(lang, tok_id, m.fertility, m.fertility, prices, fx,
                              out_in_ratio=out_in_ratio, local_currencies=local_currencies)
            local_vals = [f"{cr.costs_local.get(c, 0):.4f}" for c in local_currencies]
            table.add_row(tok_id, f"{cr.fertility:.3f}", str(cr.n_tokens),
                          f"{cr.total_cost_usd:.6f}", *local_vals)
        except Exception as e:
            table.add_row(tok_id, "[red]error[/red]", "-", "-", *["-"] * len(local_currencies))
            console.print(f"[yellow]  {tok_id}: {e}[/yellow]")

    console.print(table)


# ---------- run ----------

@app.command()
def run(
    config: str = typer.Option("configs/study_main.yaml", "--config", "-c"),
    hf_token: Optional[str] = typer.Option(None, "--hf-token", envvar="HF_TOKEN"),
    cache_dir: Optional[str] = typer.Option(None, "--cache-dir"),
    log_level: str = typer.Option("INFO", "--log-level"),
    seed: Optional[int] = typer.Option(None, "--seed"),
    max_sentences: Optional[int] = typer.Option(None, "--max-sentences", "-n",
                                                 help="Limit sentences per language (for fast test runs)."),
) -> None:
    """Run a complete study from a YAML config file."""
    _setup_globals(cache_dir=cache_dir, hf_token=hf_token, log_level=log_level)
    _register_hf(hf_token)
    _register_api()

    from afri_fertility.config import StudyConfig
    from afri_fertility.study.runner import run_study
    from afri_fertility.report.tables import write_results

    console.print(f"[bold]Loading config:[/bold] {config}")
    cfg = StudyConfig.from_yaml(config)
    if seed is not None:
        cfg = cfg.model_copy(update={"bootstrap": cfg.bootstrap.model_copy(update={"seed": seed})})
    if max_sentences is not None:
        cfg = cfg.model_copy(update={"max_sentences": max_sentences})

    console.print(f"Languages: {len(cfg.languages)} | Corpora: {len(cfg.corpora)} | Tokenizers: {len(cfg.tokenizers)}")
    with console.status("Running study..."):
        result = run_study(cfg)

    df = result.dataframe
    if df.empty:
        console.print("[yellow]No results produced. Check tokenizer/corpus availability.[/yellow]")
        raise typer.Exit(1)

    write_results(df, cfg.output_dir)
    console.print(f"\n[green]Done.[/green] {len(result.records)} records → {cfg.output_dir}")
    console.print(f"Manifest: {Path(cfg.output_dir) / 'manifest.json'}")


# ---------- figures ----------

@app.command()
def figures(
    run_dir: str = typer.Option("runs/main", "--run"),
) -> None:
    """Regenerate all 6 figures from an existing run directory."""
    import pandas as pd
    from afri_fertility.report.figures import generate_all

    results_file = Path(run_dir) / "results.parquet"
    if not results_file.exists():
        results_file = Path(run_dir) / "results.csv"
    if not results_file.exists():
        console.print(f"[red]No results file found in {run_dir}[/red]")
        raise typer.Exit(1)

    df = pd.read_parquet(results_file) if results_file.suffix == ".parquet" else pd.read_csv(results_file)
    outdir = Path(run_dir) / "figures"
    generate_all(df, outdir)
    console.print(f"[green]Figures written to {outdir}[/green]")


# ---------- leaderboard ----------

@app.command()
def leaderboard(
    run_dir: str = typer.Option("runs/main", "--run"),
    out: str = typer.Option("leaderboard.json", "--out"),
) -> None:
    """Emit leaderboard JSON from a run directory."""
    import pandas as pd
    from afri_fertility.report.leaderboard import emit_leaderboard

    results_file = Path(run_dir) / "results.parquet"
    if not results_file.exists():
        results_file = Path(run_dir) / "results.csv"

    df = pd.read_parquet(results_file) if results_file.suffix == ".parquet" else pd.read_csv(results_file)

    # Convert DataFrame rows to a list of simple namespace objects
    class Row:
        pass

    records = []
    for _, row in df.iterrows():
        r = Row()
        for col in df.columns:
            setattr(r, col, row[col])
        records.append(r)

    path = emit_leaderboard(records, out)
    console.print(f"[green]Leaderboard written to {path}[/green]")


# ---------- reproduce ----------

@app.command()
def reproduce(
    tolerance: float = typer.Option(0.05, "--tolerance", help="Allowed relative deviation from golden."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run offline reference suite and print headline premiums. No network required."""
    _register_hf()

    from pathlib import Path
    from afri_fertility.corpora.custom import CustomCorpus
    from afri_fertility.core.segmentation import segment
    from afri_fertility.core.aggregate import TextResult, aggregate_corpus
    from afri_fertility.tokenizers import REGISTRY
    from afri_fertility.tokenizers.base import UnavailableAdapter

    # Editable/source install: data/ is at project root; wheel install: bundled inside package
    _ref_candidate = Path(__file__).parents[2] / "data" / "reference_suite" / "reference.jsonl"
    ref_file = _ref_candidate if _ref_candidate.exists() else Path(__file__).parent / "data" / "reference_suite" / "reference.jsonl"
    if not ref_file.exists():
        console.print(f"[red]Reference suite not found: {ref_file}[/red]")
        raise typer.Exit(1)

    corpus = CustomCorpus(ref_file, corpus_id="reference")
    available_langs = corpus.languages()

    # Only use tokenizers that are actually available
    available_toks = [
        t for t in REGISTRY.list_all()
        if not isinstance(t, UnavailableAdapter)
    ]

    if not available_toks:
        console.print("[yellow]No tokenizers available (network-restricted? HF_TOKEN missing?).[/yellow]")
        console.print("Run 'afri-fertility tokenizers list' to see what's registered.")
        raise typer.Exit(1)

    sentences = corpus.load(available_langs)
    baseline_lang = "eng"

    results: list[dict] = []
    passes = 0
    fails = 0

    for adapter in available_toks:
        # Compute baseline fertility
        baseline_sents = sentences.get(baseline_lang, [])
        baseline_results = []
        for text in baseline_sents:
            seg = segment(text, normalization="NFC")
            n_tok = adapter.count(text)
            baseline_results.append(TextResult(tokens=n_tok, words=seg.words, chars=seg.chars, bytes=seg.bytes))

        for lang in available_langs:
            if lang == baseline_lang:
                continue
            lang_sents = sentences.get(lang, [])
            if not lang_sents:
                continue

            lang_results = []
            for text in lang_sents:
                seg = segment(text, normalization="NFC")
                n_tok = adapter.count(text)
                lang_results.append(TextResult(tokens=n_tok, words=seg.words, chars=seg.chars, bytes=seg.bytes))

            agg = aggregate_corpus(lang_results, baseline_results=baseline_results,
                                   bootstrap_n=100, seed=42)
            results.append({
                "tokenizer": adapter.id,
                "language": lang,
                "fertility": round(agg.fertility, 4),
                "premium": round(agg.premium, 4) if agg.premium else None,
            })
            passes += 1

    if json_output:
        import json
        typer.echo(json.dumps(results, indent=2))
        return

    table = Table(title="afri-fertility reproduce — Reference Suite Results")
    table.add_column("Tokenizer", style="cyan")
    table.add_column("Language")
    table.add_column("Fertility", justify="right")
    table.add_column("Premium", justify="right")

    for row in results:
        premium_str = f"{row['premium']:.3f}" if row["premium"] else "-"
        premium_color = "green" if row["premium"] and row["premium"] >= 1.0 else "yellow"
        table.add_row(
            row["tokenizer"], row["language"],
            f"{row['fertility']:.3f}",
            f"[{premium_color}]{premium_str}[/{premium_color}]",
        )

    console.print(table)
    console.print(f"\n[green]reproduce: {passes} language×tokenizer pairs measured[/green]")
    if passes > 0:
        console.print("[green]✓ PASS — reference suite completed[/green]")
    else:
        console.print("[red]✗ FAIL — no results produced[/red]")
        raise typer.Exit(1)


# ---------- registry introspection ----------

tokenizers_app = typer.Typer(help="Tokenizer registry commands.")
corpora_app = typer.Typer(help="Corpus registry commands.")
languages_app = typer.Typer(help="Language registry commands.")

app.add_typer(tokenizers_app, name="tokenizers")
app.add_typer(corpora_app, name="corpora")
app.add_typer(languages_app, name="languages")


@tokenizers_app.command("list")
def tokenizers_list(json_output: bool = typer.Option(False, "--json")) -> None:
    """List all registered tokenizers."""
    import os, logging
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    logging.getLogger("transformers").setLevel(logging.ERROR)
    _register_hf(local_only=True)  # cache-only: fast, no network calls
    _register_api()

    from afri_fertility.tokenizers import REGISTRY
    from afri_fertility.tokenizers.base import UnavailableAdapter

    if json_output:
        import json
        data = [
            {"id": a.id, "family": a.family, "vocab_size": a.vocab_size,
             "available": not isinstance(a, UnavailableAdapter)}
            for a in REGISTRY.list_all()
        ]
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title="Registered Tokenizers")
    table.add_column("ID", style="cyan")
    table.add_column("Family")
    table.add_column("Vocab size", justify="right")
    table.add_column("Status")

    for a in REGISTRY.list_all():
        status = "[green]available[/green]" if not isinstance(a, UnavailableAdapter) else "[red]unavailable[/red]"
        table.add_row(a.id, a.family, str(a.vocab_size or "-"), status)

    console.print(table)


@corpora_app.command("list")
def corpora_list(json_output: bool = typer.Option(False, "--json")) -> None:
    """List all registered corpora."""
    from afri_fertility.corpora import CORPUS_REGISTRY

    if json_output:
        import json
        data = [{"id": c.id} for c in CORPUS_REGISTRY.list_all()]
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title="Registered Corpora")
    table.add_column("ID", style="cyan")
    for c in CORPUS_REGISTRY.list_all():
        table.add_row(c.id)
    console.print(table)


@languages_app.command("list")
def languages_list(json_output: bool = typer.Option(False, "--json")) -> None:
    """List all languages in the registry."""
    from afri_fertility import languages as lang_reg

    if json_output:
        import json
        data = [
            {"iso639_3": l.iso639_3, "name": l.name, "script": l.script,
             "family": l.family, "tier": l.tier}
            for l in lang_reg.list_all()
        ]
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title="Language Registry")
    table.add_column("ISO 639-3", style="cyan")
    table.add_column("Name")
    table.add_column("Script")
    table.add_column("Family")
    table.add_column("Tier")

    for lang in lang_reg.list_all():
        table.add_row(lang.iso639_3, lang.name, lang.script, lang.family, lang.tier)

    console.print(table)


if __name__ == "__main__":
    app()
