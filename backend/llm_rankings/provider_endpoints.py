"""Persisted OpenRouter per-provider endpoint pricing and speed."""

from __future__ import annotations

from pydantic_sqlite import DataBase

from llm_rankings.combined_models import CombinedModelBase
from llm_rankings.or_endpoints import ORPercentileStats, ORPublicEndpoint
from llm_rankings.or_models import ORPricing


def provider_endpoint_row_id(model_id: str, tag: str) -> str:
    return f"{model_id}|{tag}"


class ModelProviderEndpoint(CombinedModelBase):
    """One OpenRouter provider endpoint: pricing + throughput/latency for a model."""

    id: str  # ``{model_id}|{tag}``
    model_id: str  # OpenRouter model id (catalog id we fetched)
    provider_name: str
    tag: str
    name: str

    # $/1M tokens from endpoint ``pricing`` (list rates; see ``pricing_discount``).
    pricing_input: float | None = None
    pricing_output: float | None = None
    pricing_discount: float | None = None  # multiply list price by (1 - discount)

    # Throughput: output tokens/sec over last 30m (null when OR has no sample).
    throughput_p50: float | None = None
    throughput_p75: float | None = None
    throughput_p90: float | None = None
    throughput_p99: float | None = None

    # Latency: time to first token in ms over last 30m.
    latency_p50: float | None = None
    latency_p75: float | None = None
    latency_p90: float | None = None
    latency_p99: float | None = None

    status: int | None = None
    uptime_last_30m: float | None = None
    quantization: str | None = None
    context_length: int | None = None

    def add_to_database(self, db: DataBase) -> None:
        db.add("model_provider_endpoints", self, pk="id")


def _percentile_fields(prefix: str, stats: ORPercentileStats | None) -> dict[str, float | None]:
    if stats is None:
        return {
            f"{prefix}_p50": None,
            f"{prefix}_p75": None,
            f"{prefix}_p90": None,
            f"{prefix}_p99": None,
        }
    return {
        f"{prefix}_p50": stats.p50,
        f"{prefix}_p75": stats.p75,
        f"{prefix}_p90": stats.p90,
        f"{prefix}_p99": stats.p99,
    }


def from_or_public_endpoint(
    endpoint: ORPublicEndpoint,
    *,
    model_id: str,
) -> ModelProviderEndpoint:
    """Map an API endpoint onto a DB row. ``model_id`` is the catalog id we requested."""
    pricing: ORPricing = endpoint.pricing
    return ModelProviderEndpoint(
        id=provider_endpoint_row_id(model_id, endpoint.tag),
        model_id=model_id,
        provider_name=endpoint.provider_name,
        tag=endpoint.tag,
        name=endpoint.name,
        pricing_input=ORPricing.get_per_million_tokens(pricing.prompt),
        pricing_output=ORPricing.get_per_million_tokens(pricing.completion),
        pricing_discount=pricing.discount,
        **_percentile_fields("throughput", endpoint.throughput_last_30m),
        **_percentile_fields("latency", endpoint.latency_last_30m),
        status=endpoint.status,
        uptime_last_30m=endpoint.uptime_last_30m,
        quantization=endpoint.quantization,
        context_length=endpoint.context_length,
    )
