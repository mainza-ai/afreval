use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct HarnessPins {
    pub afri_fertility_pin: String,
    pub afrobench_lite_pin: String,
    pub waxal_pin: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct LinguisticFidelity {
    pub waxal_macro_wer: f64,
    pub afrobench_lite_accuracy: f64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CulturalSafety {
    pub bias_corrected_judge_score: f64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct StructuralEconomics {
    pub mean_fertility_premium: f64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ModelReport {
    pub model_id: String,
    pub harness: HarnessPins,
    pub linguistic_fidelity: LinguisticFidelity,
    pub cultural_safety: CulturalSafety,
    pub structural_economics: StructuralEconomics,
}

impl ModelReport {
    pub fn from_json(s: &str) -> Result<Self, String> {
        serde_json::from_str(s).map_err(|e| e.to_string())
    }

    pub fn validate(&self) -> Result<(), String> {
        let wer = self.linguistic_fidelity.waxal_macro_wer;
        if !(0.0..=1.0).contains(&wer) {
            return Err(format!("waxal_macro_wer out of range [0,1]: {wer}"));
        }
        let acc = self.linguistic_fidelity.afrobench_lite_accuracy;
        if !(0.0..=1.0).contains(&acc) {
            return Err(format!("afrobench_lite_accuracy out of range [0,1]: {acc}"));
        }
        let judge = self.cultural_safety.bias_corrected_judge_score;
        if !(0.0..=100.0).contains(&judge) {
            return Err(format!("bias_corrected_judge_score out of range [0,100]: {judge}"));
        }
        let premium = self.structural_economics.mean_fertility_premium;
        if premium < 1.0 {
            return Err(format!("mean_fertility_premium must be >= 1.0 (English baseline): {premium}"));
        }
        if self.model_id.trim().is_empty() {
            return Err("model_id must not be empty".into());
        }
        Ok(())
    }
}
