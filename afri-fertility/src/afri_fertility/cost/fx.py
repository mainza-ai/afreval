"""FX table loading and currency conversion."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


class FXTable:
    def __init__(self, snapshot_date: str, base: str, rates: dict[str, float]) -> None:
        self.snapshot_date = snapshot_date
        self.base = base
        self._rates = rates

    @classmethod
    def from_yaml(cls, path: str | Path) -> "FXTable":
        data = yaml.safe_load(Path(path).read_text())
        return cls(
            snapshot_date=data["snapshot_date"],
            base=data.get("base", "USD"),
            rates=data["rates"],
        )

    def convert(self, amount_usd: float, currency: str) -> float:
        """Convert USD amount to target currency."""
        if currency == self.base:
            return amount_usd
        try:
            return amount_usd * self._rates[currency]
        except KeyError:
            raise KeyError(
                f"No FX rate for '{currency}'. Available: {sorted(self._rates.keys())}"
            )

    def list_currencies(self) -> list[str]:
        return sorted(self._rates.keys())

    def __contains__(self, currency: str) -> bool:
        return currency in self._rates


def _find_default_fx_file() -> Path:
    # Editable/source install: configs/ is at project root (three levels above cost/)
    candidate = Path(__file__).parents[3] / "configs" / "fx_2026-06.yaml"
    if candidate.exists():
        return candidate
    # Wheel install: defaults are bundled inside the package
    return Path(__file__).parents[1] / "_defaults" / "fx_2026-06.yaml"


_DEFAULT_FX_FILE = _find_default_fx_file()


@lru_cache(maxsize=4)
def load_default_fx() -> FXTable:
    return FXTable.from_yaml(_DEFAULT_FX_FILE)
