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
        call: Option<PathBuf>,
        #[arg(long)]
        batch: bool,
    },
    Grant {
        #[arg(long)]
        policy: PathBuf,
        #[arg(long)]
        tool: String,
        #[arg(long, name = "age-secs")]
        age_secs: u64,
        #[arg(long)]
        call_hash: Option<String>,
    },
    Sanitize {
        #[arg(long)]
        policy: PathBuf,
    },
}

fn load_policy(path: &PathBuf) -> Result<Policy, String> {
    let s = fs::read_to_string(path).map_err(|e| format!("read {}: {e}", path.display()))?;
    serde_json::from_str(&s).map_err(|e| e.to_string())
}

fn run(cli: Cli) -> i32 {
    match cli.cmd {
        Cmd::Validate { policy, call, batch } => {
            let policy = match load_policy(&policy) {
                Ok(p) => p,
                Err(e) => {
                    eprintln!("error: {e}");
                    return 2;
                }
            };
            if batch {
                return validate_batch(&policy);
            }
            let call_path = match call {
                Some(p) => p,
                None => {
                    eprintln!("error: --call required unless --batch");
                    return 2;
                }
            };
            let cs = match fs::read_to_string(&call_path) {
                Ok(s) => s,
                Err(e) => {
                    eprintln!("error: read {}: {e}", call_path.display());
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
        Cmd::Grant { policy, tool, age_secs, call_hash } => {
            let policy = match load_policy(&policy) {
                Ok(p) => p,
                Err(e) => {
                    eprintln!("error: {e}");
                    return 2;
                }
            };
            let iat = clearance::now_secs().saturating_sub(age_secs);
            let result = match call_hash {
                Some(h) => clearance::sign_for_call(&tool, &h, iat, &policy.clearance),
                None => clearance::sign(&tool, iat, &policy.clearance),
            };
            match result {
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
        Cmd::Sanitize { policy } => {
            use std::io::Read;
            let policy = match load_policy(&policy) {
                Ok(p) => p,
                Err(e) => {
                    eprintln!("error: {e}");
                    return 2;
                }
            };
            let mut buf = Vec::new();
            if std::io::stdin().read_to_end(&mut buf).is_err() {
                eprintln!("error: read stdin");
                return 2;
            }
            match afreval_airlock::sanitize_output(&buf, &policy) {
                Ok(masked) => {
                    println!("{}", String::from_utf8_lossy(&masked));
                    0
                }
                Err(e) => {
                    eprintln!("error: {e}");
                    1
                }
            }
        }
    }
}

fn validate_batch(policy: &Policy) -> i32 {
    use std::io::Read;
    let mut buf = String::new();
    if std::io::stdin().read_to_string(&mut buf).is_err() {
        eprintln!("error: read stdin");
        return 2;
    }
    let calls: Vec<ToolCall> = match serde_json::from_str(&buf) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("error: {e}");
            return 2;
        }
    };
    let now = clearance::now_secs();
    let mut guard = clearance::ReplayGuard::new();
    let verdicts: Vec<_> = calls
        .iter()
        .map(|c| afreval_airlock::validate_guarded(c, policy, now, &mut guard))
        .collect();
    println!("{}", serde_json::to_string_pretty(&verdicts).unwrap());
    0
}

fn main() {
    let cli = Cli::parse();
    std::process::exit(run(cli));
}
