"""Cost computation: tokens → USD → local currency."""
from __future__ import annotations

from dataclasses import dataclass, field

from .prices import PriceTable, load_default_prices
from .fx import FXTable, load_default_fx


@dataclass
class CostResult:
    language: str
    tokenizer: str
    fertility: float
    n_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    relative_cost: float   # ≈ premium
    costs_local: dict[str, float] = field(default_factory=dict)


@dataclass
class AnnualizedTax:
    scenario: str
    language: str
    tokenizer: str
    monthly_queries: int
    annual_premium_usd: float
    annual_premium_local: dict[str, float] = field(default_factory=dict)


def compute_cost(
    language: str,
    tokenizer_id: str,
    fertility: float,
    baseline_fertility: float,
    prices: PriceTable | None = None,
    fx: FXTable | None = None,
    reference_words: int = 1000,
    out_in_ratio: float = 1.0,
    local_currencies: list[str] | None = None,
) -> CostResult:
    """
    Compute input, output, and total cost for reference_words words of meaning in language L.

    Cost model (pre-registered):
        tokens(L,T)     = reference_words × F(L,T)
        input_cost      = tokens × price_in
        output_cost     = tokens × out_in_ratio × price_out
        total_cost      = input_cost + output_cost
        relative_cost   ≈ premium = F(L,T) / F(eng,T)
    """
    if prices is None:
        prices = load_default_prices()
    if fx is None:
        fx = load_default_fx()
    if local_currencies is None:
        local_currencies = ["NGN", "ZAR", "KES"]

    model_price = prices.get(tokenizer_id)
    n_tokens = int(reference_words * fertility)
    input_cost = n_tokens * model_price.price_in
    output_cost = n_tokens * out_in_ratio * model_price.price_out
    total_cost = input_cost + output_cost

    relative_cost = fertility / baseline_fertility if baseline_fertility > 0 else 0.0

    costs_local = {
        currency: fx.convert(total_cost, currency)
        for currency in local_currencies
        if currency in fx
    }

    return CostResult(
        language=language,
        tokenizer=tokenizer_id,
        fertility=fertility,
        n_tokens=n_tokens,
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        total_cost_usd=total_cost,
        relative_cost=relative_cost,
        costs_local=costs_local,
    )


def annualized_tax(
    cost_result: CostResult,
    baseline_cost: CostResult,
    monthly_queries: int,
    scenario_name: str = "default",
    fx: FXTable | None = None,
    local_currencies: list[str] | None = None,
) -> AnnualizedTax:
    """Compute the annualized extra cost vs baseline for a deployment scenario."""
    if fx is None:
        fx = load_default_fx()
    if local_currencies is None:
        local_currencies = ["NGN", "ZAR", "KES"]

    annual_queries = monthly_queries * 12
    annual_extra_usd = (cost_result.total_cost_usd - baseline_cost.total_cost_usd) * annual_queries

    annual_local = {
        currency: fx.convert(annual_extra_usd, currency)
        for currency in local_currencies
        if currency in fx
    }

    return AnnualizedTax(
        scenario=scenario_name,
        language=cost_result.language,
        tokenizer=cost_result.tokenizer,
        monthly_queries=monthly_queries,
        annual_premium_usd=annual_extra_usd,
        annual_premium_local=annual_local,
    )
