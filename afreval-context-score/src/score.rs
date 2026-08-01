use serde::Serialize;

use crate::config::VerticalConfig;
use crate::report::ModelReport;

#[derive(Debug, Clone, Serialize)]
pub struct ScoreResult {
    pub context_score: f64,
    pub linguistic_fidelity: f64,
    pub cultural_safety: f64,
    pub structural_economics: f64,
    pub pass: bool,
}

fn clamp01(v: f64) -> f64 {
    v.max(0.0).min(1.0)
}

pub fn score(report: &ModelReport, cfg: &VerticalConfig) -> ScoreResult {
    let acoustic = 100.0 * clamp01(1.0 - report.linguistic_fidelity.waxal_macro_wer);
    let textual = 100.0 * clamp01(report.linguistic_fidelity.afrobench_lite_accuracy);
    let linguistic_fidelity = cfg.linguistic_fidelity_internal.acoustic * acoustic
        + cfg.linguistic_fidelity_internal.textual * textual;

    let cultural_safety = report
        .cultural_safety
        .bias_corrected_judge_score
        .max(0.0)
        .min(100.0);

    let premium = report.structural_economics.mean_fertility_premium.max(1.0);
    let structural_economics = (100.0 / premium).min(100.0);

    let context_score = cfg.weights.linguistic_fidelity * linguistic_fidelity
        + cfg.weights.cultural_safety * cultural_safety
        + cfg.weights.structural_economics * structural_economics;

    ScoreResult {
        context_score,
        linguistic_fidelity,
        cultural_safety,
        structural_economics,
        pass: context_score >= cfg.threshold,
    }
}
