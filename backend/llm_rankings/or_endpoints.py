"""OpenRouter model-endpoints API shapes (``GET /models/{author}/{slug}/endpoints``).

Field required/optional (and nullability) follow OpenRouter OpenAPI schemas
``ListEndpointsResponse`` / ``PublicEndpoint`` in ``api-docs/openapi-openrouter.json``.
"""

from __future__ import annotations

from pydantic import ConfigDict

from llm_rankings.or_models import ORArchitecture, ORBaseModel, ORPricing


class ORPercentileStats(ORBaseModel):
    """Latency (ms TTFT) or throughput (tokens/sec) percentiles over the last 30 minutes."""

    p50: float
    p75: float
    p90: float
    p99: float


class ORToolChoiceSupport(ORBaseModel):
    none: bool
    auto: bool
    required: bool
    function: bool


class ORWorkloadPerf(ORBaseModel):
    latency: ORPercentileStats | None = None
    throughput: ORPercentileStats | None = None
    request_count: int | None = None


class ORPerfByWorkload(ORBaseModel):
    """Auth-only additive perf breakdown; ignore unknown workload keys from upstream."""

    model_config = ConfigDict(extra="ignore")

    text_generation: ORWorkloadPerf | None = None
    image_generation: ORWorkloadPerf | None = None
    video_generation: ORWorkloadPerf | None = None
    embeddings: ORWorkloadPerf | None = None
    decisions: ORWorkloadPerf | None = None
    speech: ORWorkloadPerf | None = None
    transcription: ORWorkloadPerf | None = None
    rerank: ORWorkloadPerf | None = None


class ORPublicEndpoint(ORBaseModel):
    """One hosting provider endpoint for a model (OpenAPI ``PublicEndpoint``)."""

    name: str
    model_id: str
    model_name: str
    context_length: int
    pricing: ORPricing
    provider_name: str
    tag: str
    quantization: str | None
    max_completion_tokens: int | None
    max_prompt_tokens: int | None
    supported_parameters: list[str]
    supports_tool_choice: ORToolChoiceSupport
    uptime_last_30m: float | None
    uptime_last_5m: float | None
    uptime_last_1d: float | None
    supports_implicit_caching: bool
    latency_last_30m: ORPercentileStats | None
    throughput_last_30m: ORPercentileStats | None
    status: int | None = None
    supports_image_reference: bool = False
    supports_multiple_audio_references: bool = False
    supports_voice_cloning: bool = False
    perf_last_30m_by_workload: ORPerfByWorkload | None = None


class ORListEndpointsData(ORBaseModel):
    """OpenAPI ``ListEndpointsResponse`` (the inner ``data`` object)."""

    id: str
    name: str
    created: int
    description: str
    architecture: ORArchitecture
    endpoints: list[ORPublicEndpoint]


class OREndpointsAPIResponse(ORBaseModel):
    data: ORListEndpointsData


def split_model_id(model_id: str) -> tuple[str, str]:
    """Split ``author/slug`` (slug may contain ``/`` or variant suffixes)."""
    author, _, slug = model_id.partition("/")
    if not author or not slug:
        raise ValueError(f"Invalid OpenRouter model id (expected author/slug): {model_id!r}")
    return author, slug


def endpoints_path_for_model(model_id: str) -> str:
    author, slug = split_model_id(model_id)
    return f"/models/{author}/{slug}/endpoints"
