"""Context Profile — the per-language/per-script/dimension breakdown behind the
scalar Context Score (review-remediation R1, 2026-08-05).

The scalar Context Score is a rollup. This module assembles the VECTOR view the
reviews demand: per-language fertility/premium/WER, per-script premiums, and the
three scored dimensions — so a model can't "pass on aggregate while failing in
Wolof health contexts." Everything here is assembled from data the frozen
harnesses already produce; the Rust scorer core is untouched.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

from .tokenizer_eval import TokenizerEvalResult


def build_profile(
    tokenizer_result: TokenizerEvalResult,
    *,
    waxal_per_language_wer: dict[str, float] | None = None,
    bias_corrected_judge_score: float | None = None,
    re_cert_after_days: int = 90,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Assemble the Context Profile vector.

    Args:
        tokenizer_result: §3.1 tokenizer eval result (per-language premiums).
        waxal_per_language_wer: {lang: macro WER} from the QA baseline (optional;
            only the 18 covered languages).
        bias_corrected_judge_score: the §3.3-corrected judge score (optional).
        re_cert_after_days: recommended re-certification cadence for the vertical.
        as_of: cert date (default today).
    """
    as_of = as_of or _dt.date.today().isoformat()

    languages: dict[str, dict[str, float]] = {}
    for row in tokenizer_result.languages:
        languages[row.lang] = {
            "fertility": round(row.fertility, 4),
            "cpt": round(row.cpt, 4),
            "premium": round(row.premium, 4) if row.premium is not None else 1.0,
        }
    if waxal_per_language_wer:
        for lang, wer in waxal_per_language_wer.items():
            languages.setdefault(lang, {})["wer"] = round(wer, 4)

    scripts = {s: round(v, 4) for s, v in tokenizer_result.script_premiums().items() if v is not None}

    dimensions: dict[str, float] = {}
    if tokenizer_result.english_cpt is not None:
        dimensions["english_cpt"] = round(tokenizer_result.english_cpt, 4)
    if bias_corrected_judge_score is not None:
        dimensions["cultural_safety_judge"] = round(bias_corrected_judge_score, 4)

    re_cert_after = (as_of and _dt.date.fromisoformat(as_of)
                     + _dt.timedelta(days=re_cert_after_days)).isoformat() if as_of else None

    return {
        "languages": languages,
        "scripts": scripts,
        "dimensions": dimensions,
        "as_of": as_of,
        "re_cert_after": re_cert_after,
    }


def cert_age_days(cert: dict) -> int:
    """Days since the cert's as_of date (0 if unknown)."""
    as_of = cert.get("as_of") or (cert.get("profile") or {}).get("as_of")
    if not as_of:
        return 0
    try:
        return (_dt.date.today() - _dt.date.fromisoformat(as_of)).days
    except ValueError:
        return 0


def is_stale(cert: dict) -> bool:
    """True when a cert is past its recommended re-certification date."""
    re_cert_after = (cert.get("profile") or {}).get("re_cert_after")
    if not re_cert_after:
        return False
    try:
        return _dt.date.today() > _dt.date.fromisoformat(re_cert_after)
    except ValueError:
        return False
