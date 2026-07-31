"""Pydantic StudyConfig and related models."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class BootstrapConfig(BaseModel):
    iterations: int = 1000
    seed: int = 42


class ScenarioConfig(BaseModel):
    out_in_ratio: float = 1.0
    monthly_queries: int = 1_000_000


class CostConfig(BaseModel):
    prices: str = "configs/prices_2026-06.yaml"
    fx: str = "configs/fx_2026-06.yaml"
    reference_words: int = 1000
    scenarios: dict[str, ScenarioConfig] = Field(default_factory=dict)


class CorpusSpec(BaseModel):
    id: str
    split: str = "devtest"


class StudyConfig(BaseModel):
    baseline_language: str = "eng"
    languages: list[str] = Field(default_factory=list)
    corpora: list[CorpusSpec] = Field(default_factory=list)
    tokenizers: list[str] = Field(default_factory=list)
    normalization: str = "NFC"
    segmentation: str = "uax29"
    bootstrap: BootstrapConfig = Field(default_factory=BootstrapConfig)
    context_window: int = 128_000
    cost: CostConfig = Field(default_factory=CostConfig)
    accuracy_table: str | None = None
    output_dir: str = "runs/main"
    workers: int = 4
    max_sentences: int | None = None

    @classmethod
    def from_yaml(cls, path: str | Path) -> "StudyConfig":
        data = yaml.safe_load(Path(path).read_text())
        return cls.model_validate(data)

    @model_validator(mode="before")
    @classmethod
    def _coerce_corpora(cls, values: Any) -> Any:
        if isinstance(values, dict) and "corpora" in values:
            corpora = values["corpora"]
            coerced = []
            for c in corpora:
                if isinstance(c, str):
                    coerced.append({"id": c})
                else:
                    coerced.append(c)
            values["corpora"] = coerced
        return values
