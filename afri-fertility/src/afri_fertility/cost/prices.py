"""Price table loading and snapshot pinning."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ModelPrice:
    tokenizer_id: str
    price_in: float   # USD per token
    price_out: float  # USD per token


class PriceTable:
    def __init__(self, snapshot_date: str, currency: str, prices: dict[str, ModelPrice]) -> None:
        self.snapshot_date = snapshot_date
        self.currency = currency
        self._prices = prices

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PriceTable":
        data = yaml.safe_load(Path(path).read_text())
        prices = {
            tok_id: ModelPrice(
                tokenizer_id=tok_id,
                price_in=model["price_in"],
                price_out=model["price_out"],
            )
            for tok_id, model in data["models"].items()
        }
        return cls(
            snapshot_date=data["snapshot_date"],
            currency=data.get("currency", "USD"),
            prices=prices,
        )

    def get(self, tokenizer_id: str) -> ModelPrice:
        try:
            return self._prices[tokenizer_id]
        except KeyError:
            raise KeyError(
                f"No price entry for tokenizer '{tokenizer_id}'. "
                f"Available: {sorted(self._prices.keys())}"
            )

    def list_tokenizer_ids(self) -> list[str]:
        return sorted(self._prices.keys())

    def __contains__(self, tokenizer_id: str) -> bool:
        return tokenizer_id in self._prices


def _find_default_prices_file() -> Path:
    # Editable/source install: configs/ is at project root (three levels above cost/)
    candidate = Path(__file__).parents[3] / "configs" / "prices_2026-06.yaml"
    if candidate.exists():
        return candidate
    # Wheel install: defaults are bundled inside the package
    return Path(__file__).parents[1] / "_defaults" / "prices_2026-06.yaml"


_DEFAULT_PRICES_FILE = _find_default_prices_file()


@lru_cache(maxsize=4)
def load_default_prices() -> PriceTable:
    return PriceTable.from_yaml(_DEFAULT_PRICES_FILE)
