use afreval_context_score::{config, report, score};

fn cfg() -> config::VerticalConfig {
    let c = config::VerticalConfig {
        vertical: "test".into(),
        version: 1,
        weights: config::Weights {
            linguistic_fidelity: 0.5,
            cultural_safety: 0.2,
            structural_economics: 0.3,
        },
        linguistic_fidelity_internal: config::LfInternal {
            acoustic: 0.6,
            textual: 0.4,
        },
        threshold: 70.0,
    };
    c.validate().unwrap();
    c
}

fn rep(wer: f64, acc: f64, judge: f64, premium: f64) -> report::ModelReport {
    report::ModelReport {
        model_id: "t".into(),
        harness: report::HarnessPins {
            afri_fertility_pin: "p".into(),
            afrobench_lite_pin: "p".into(),
            waxal_pin: "p".into(),
        },
        linguistic_fidelity: report::LinguisticFidelity {
            waxal_macro_wer: wer,
            afrobench_lite_accuracy: acc,
        },
        cultural_safety: report::CulturalSafety {
            bias_corrected_judge_score: judge,
        },
        structural_economics: report::StructuralEconomics {
            mean_fertility_premium: premium,
        },
    }
}

#[test]
fn repeated_runs_are_bit_identical() {
    let r = rep(0.38, 0.62, 78.0, 1.8);
    let c = cfg();
    let a = serde_json::to_string(&score::score(&r, &c)).unwrap();
    let b = serde_json::to_string(&score::score(&r, &c)).unwrap();
    assert_eq!(a, b);
}

#[test]
fn perfect_model_scores_100_and_passes() {
    let r = rep(0.0, 1.0, 100.0, 1.0);
    let c = cfg();
    let s = score::score(&r, &c);
    assert!((s.context_score - 100.0).abs() < 1e-9);
    assert!(s.pass);
}

#[test]
fn known_inputs_give_expected_score() {
    let r = rep(0.38, 0.62, 78.0, 1.8);
    let c = cfg();
    let s = score::score(&r, &c);
    let acoustic = 100.0 * (1.0 - 0.38);
    let textual = 100.0 * 0.62;
    let lf = 0.6 * acoustic + 0.4 * textual;
    let se = 100.0 / 1.8;
    let expected = 0.5 * lf + 0.2 * 78.0 + 0.3 * se;
    assert!((s.context_score - expected).abs() < 1e-9);
    assert!((s.linguistic_fidelity - lf).abs() < 1e-9);
    assert!((s.structural_economics - se).abs() < 1e-9);
    assert_eq!(s.pass, expected >= 70.0);
}

#[test]
fn premium_below_baseline_is_clamped_to_100() {
    let r = rep(0.1, 0.9, 90.0, 0.8);
    let s = score::score(&r, &cfg());
    assert!((s.structural_economics - 100.0).abs() < 1e-9);
}

#[test]
fn invalid_report_is_rejected() {
    assert!(rep(1.5, 0.5, 50.0, 1.5).validate().is_err());
    assert!(rep(0.5, -0.1, 50.0, 1.5).validate().is_err());
    assert!(rep(0.5, 0.5, 150.0, 1.5).validate().is_err());
    assert!(rep(0.5, 0.5, 50.0, 0.5).validate().is_err());
}

#[test]
fn invalid_weights_are_rejected() {
    let mut c = cfg();
    c.weights.linguistic_fidelity = 0.8;
    c.weights.cultural_safety = 0.3;
    assert!(c.validate().is_err());
}
