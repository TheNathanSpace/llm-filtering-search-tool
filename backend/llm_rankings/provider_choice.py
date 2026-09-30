"""Pick one OpenRouter provider per model for listed price and median speed."""

from __future__ import annotations

import math

from llm_rankings.combined_models import CombinedModel
from llm_rankings.provider_endpoints import ModelProviderEndpoint

# Token share for listed $/1M rates: Artificial Analysis general-agentic mix
# (7 cached + 2 fresh input, 1 output) with cache billed as ordinary input.
INPUT_WEIGHT = 0.90
OUTPUT_WEIGHT = 0.10

# Skip the cheapest only when it is worse than the next on both of these.
LATENCY_WORSE_RATIO = 2.0
THROUGHPUT_WORSE_RATIO = 0.5


def _priced(endpoints: list[ModelProviderEndpoint]) -> list[ModelProviderEndpoint]:
    return [
        endpoint
        for endpoint in endpoints
        if endpoint.pricing_input is not None and endpoint.pricing_output is not None
    ]


def _rank_key(endpoint: ModelProviderEndpoint) -> tuple[float, float, float]:
    """Cheapest listed blend, then lower latency, then higher throughput."""
    assert endpoint.pricing_input is not None and endpoint.pricing_output is not None
    cost = INPUT_WEIGHT * endpoint.pricing_input + OUTPUT_WEIGHT * endpoint.pricing_output
    latency = endpoint.latency_p50 if endpoint.latency_p50 is not None else math.inf
    throughput = endpoint.throughput_p50 if endpoint.throughput_p50 is not None else -math.inf
    return (cost, latency, -throughput)


def _much_worse(cheapest: ModelProviderEndpoint, nxt: ModelProviderEndpoint) -> bool:
    """True when cheapest is >2× slower to first token and <½ the throughput."""
    if (
        cheapest.latency_p50 is None
        or cheapest.throughput_p50 is None
        or nxt.latency_p50 is None
        or nxt.throughput_p50 is None
    ):
        return False
    return (
        cheapest.latency_p50 > LATENCY_WORSE_RATIO * nxt.latency_p50
        and cheapest.throughput_p50 < THROUGHPUT_WORSE_RATIO * nxt.throughput_p50
    )


def choose_provider(endpoints: list[ModelProviderEndpoint]) -> ModelProviderEndpoint | None:
    """Return the provider to show for price and speed, or None when none are priced.

    Rank by listed ``0.90 * input + 0.10 * output`` ($/1M). Discount and cache-read
    prices are ignored. Take the cheapest. If the next endpoint has both median
    speed stats and the cheapest is much worse on both latency and throughput, use
    the next one. Do not look past that pair.
    """
    ranked = sorted(_priced(endpoints), key=_rank_key)
    if not ranked:
        return None
    chosen = ranked[0]
    if len(ranked) > 1 and _much_worse(chosen, ranked[1]):
        return ranked[1]
    return chosen


def apply_provider_choice(
    models: list[CombinedModel],
    endpoints: list[ModelProviderEndpoint],
) -> None:
    """Write the chosen provider's list prices and p50 speed onto each model."""
    by_model: dict[str, list[ModelProviderEndpoint]] = {}
    for endpoint in endpoints:
        by_model.setdefault(endpoint.model_id, []).append(endpoint)
    for model in models:
        chosen = choose_provider(by_model.get(model.id, []))
        if chosen is None:
            continue
        model.pricing_input = chosen.pricing_input
        model.pricing_output = chosen.pricing_output
        model.throughput = chosen.throughput_p50
        model.latency_ms = chosen.latency_p50
        model.selected_provider = chosen.provider_name
