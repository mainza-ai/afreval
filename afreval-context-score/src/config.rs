use serde::Deserialize;

pub const WEIGHT_SUM_EPS: f64 = 1e-6;

#[derive(Debug, Clone, Deserialize)]
pub struct Weights {
    pub linguistic_fidelity: f64,
    pub cultural_safety: f64,
    pub structural_economics: f64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct LfInternal {
    pub acoustic: f64,
    pub textual: f64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct VerticalConfig {
    pub vertical: String,
    pub version: u32,
    pub weights: Weights,
    pub linguistic_fidelity_internal: LfInternal,
    pub threshold: f64,
}

impl VerticalConfig {
    pub fn from_yaml(s: &str) -> Result<Self, String> {
        serde_yaml::from_str(s).map_err(|e| e.to_string())
    }

    pub fn validate(&self) -> Result<(), String> {
        let top = self.weights.linguistic_fidelity
            + self.weights.cultural_safety
            + self.weights.structural_economics;
        if (top - 1.0).abs() > WEIGHT_SUM_EPS {
            return Err(format!(
                "top-level weights must sum to 1.0 (got {top}); calibration loop owns weight search"
            ));
        }
        let lf = self.linguistic_fidelity_internal.acoustic
            + self.linguistic_fidelity_internal.textual;
        if (lf - 1.0).abs() > WEIGHT_SUM_EPS {
            return Err(format!(
                "linguistic_fidelity_internal must sum to 1.0 (got {lf})"
            ));
        }
        for w in [
            self.weights.linguistic_fidelity,
            self.weights.cultural_safety,
            self.weights.structural_economics,
            self.linguistic_fidelity_internal.acoustic,
            self.linguistic_fidelity_internal.textual,
        ] {
            if !(0.0..=1.0).contains(&w) {
                return Err(format!("weight out of range [0,1]: {w}"));
            }
        }
        if !(0.0..=100.0).contains(&self.threshold) {
            return Err(format!("threshold out of range [0,100]: {}", self.threshold));
        }
        Ok(())
    }
}
