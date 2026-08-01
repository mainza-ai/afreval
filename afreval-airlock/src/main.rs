use std::fs;
use std::path::PathBuf;

use afreval_airlock::{clearance, Policy, ToolCall};
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "afreval-airlock", version, about = "Deny-by-default tool-call validator (§3.5)")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Validate {
        #[arg(long)]
        policy: PathBuf,
        #[arg(long)]
        call: PathBuf,
    },
    Grant {
        #[arg(long)]
        policy: PathBuf,
        #[arg(long)]
        tool: String,
        #[arg(long, name = "age-secs")]
        age_secs: u64,
    },
}

fn load_policy(path: &PathBuf) -> Result<Policy, String> {
    let s = fs::read_to_string(path).map_err(|e| format!("read {}: {e}", path.display()))?;
    serde_json::from_str(&s).map_err(|e| e.to_string())
}

fn run(cli: Cli) -> i32 {
    match cli.cmd {
        Cmd::Validate { policy, call } => {
            let policy = match load_policy(&policy) {
                Ok(p) => p,
                Err(e) => {
                    eprintln!("error: {e}");
                    return 2;
                }
            };
            let cs = match fs::read_to_string(&call) {
                Ok(s) => s,
                Err(e) => {
                    eprintln!("error: read {}: {e}", call.display());
                    return 2;
                }
            };
            let call: ToolCall = match serde_json::from_str(&cs) {
                Ok(c) => c,
                Err(e) => {
                    eprintln!("error: {e}");
                    return 2;
                }
            };
            let verdict = afreval_airlock::validate(&call, &policy, clearance::now_secs());
            println!("{}", serde_json::to_string_pretty(&verdict).unwrap());
            if verdict.is_allowed() {
                0
            } else {
                1
            }
        }
        Cmd::Grant { policy, tool, age_secs } => {
            let policy = match load_policy(&policy) {
                Ok(p) => p,
                Err(e) => {
                    eprintln!("error: {e}");
                    return 2;
                }
            };
            match clearance::sign(&tool, clearance::now_secs().saturating_sub(age_secs), &policy.clearance) {
                Ok(g) => {
                    println!("{g}");
                    0
                }
                Err(e) => {
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
