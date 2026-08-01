use std::fs;
use std::path::PathBuf;

use afreval_context_score::{config, report, score};
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "afreval-context-score", version, about = "Deterministic Context Score scorer (§3.2, Phase 1)")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Score {
        #[arg(long)]
        report: PathBuf,
        #[arg(long)]
        weights: PathBuf,
    },
    Validate {
        #[arg(long)]
        report: PathBuf,
        #[arg(long)]
        weights: PathBuf,
    },
}

fn load_report(path: &PathBuf) -> Result<report::ModelReport, String> {
    let s = fs::read_to_string(path).map_err(|e| format!("read {}: {e}", path.display()))?;
    let r = report::ModelReport::from_json(&s)?;
    r.validate()?;
    Ok(r)
}

fn load_weights(path: &PathBuf) -> Result<config::VerticalConfig, String> {
    let s = fs::read_to_string(path).map_err(|e| format!("read {}: {e}", path.display()))?;
    let c = config::VerticalConfig::from_yaml(&s)?;
    c.validate()?;
    Ok(c)
}

fn run(cli: Cli) -> i32 {
    match cli.cmd {
        Cmd::Score { report, weights } => {
            let r = match load_report(&report) {
                Ok(r) => r,
                Err(e) => {
                    eprintln!("error: {e}");
                    return 2;
                }
            };
            let c = match load_weights(&weights) {
                Ok(c) => c,
                Err(e) => {
                    eprintln!("error: {e}");
                    return 2;
                }
            };
            let result = score::score(&r, &c);
            let out = serde_json::json!({
                "model_id": r.model_id,
                "vertical": c.vertical,
                "weights_version": c.version,
                "threshold": c.threshold,
                "context_score": result.context_score,
                "vectors": {
                    "linguistic_fidelity": result.linguistic_fidelity,
                    "cultural_safety": result.cultural_safety,
                    "structural_economics": result.structural_economics,
                },
                "pass": result.pass,
            });
            println!("{}", serde_json::to_string_pretty(&out).unwrap());
            if result.pass {
                0
            } else {
                1
            }
        }
        Cmd::Validate { report, weights } => {
            match (load_report(&report), load_weights(&weights)) {
                (Ok(_), Ok(_)) => {
                    println!("ok");
                    0
                }
                (Err(e), _) | (_, Err(e)) => {
                    eprintln!("error: {e}");
                    2
                }
            }
        }
    }
}

fn main() {
    let cli = Cli::parse();
    std::process::exit(run(cli));
}
