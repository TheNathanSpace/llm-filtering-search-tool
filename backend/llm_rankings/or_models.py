import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class ORBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @staticmethod
    def optional_field(key: str, value: Any) -> dict[str, Any]:
        return {key: value} if value else {}


# https://openrouter.ai/docs/api/api-reference/models/get-models
# Field required/optional (and nullability) follow OpenRouter Models API schemas
# (Model / ModelsListResponse and nested types) in api-docs/openapi-openrouter.json.


class InputModality(StrEnum):
    """OpenAPI `InputModality`."""

    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"


class OutputModality(StrEnum):
    """OpenAPI `OutputModality`."""

    TEXT = "text"
    IMAGE = "image"
    EMBEDDINGS = "embeddings"
    AUDIO = "audio"
    VIDEO = "video"
    RERANK = "rerank"
    SPEECH = "speech"
    TRANSCRIPTION = "transcription"


class ORPricingOverride(ORBaseModel):
    """Conditional override of base pricing (token threshold and/or UTC window)."""

    min_prompt_tokens: float | None = None
    utc_start: float | None = None
    utc_end: float | None = None
    utc_days: list[str] | None = None
    prompt: float | None = None
    completion: float | None = None
    audio: float | None = None
    input_cache_read: float | None = None
    input_cache_write: float | None = None
    input_cache_write_1h: float | None = None
    input_audio_cache: float | None = None


class ORPricing(ORBaseModel):
    """Prices are in $/token, NOT $/1M tokens."""

    prompt: float
    completion: float
    image: float | None = None
    audio: float | None = None
    request: float | None = None
    web_search: float | None = None
    internal_reasoning: float | None = None
    input_cache_read: float | None = None
    input_cache_write: float | None = None
    input_cache_write_1h: float | None = None
    audio_output: float | None = None
    image_output: float | None = None
    image_token: float | None = None
    input_audio_cache: float | None = None
    discount: float | None = None
    overrides: list[ORPricingOverride] | None = None

    @staticmethod
    def get_per_million_tokens(value: float | None) -> float | None:
        if value is None:
            return None
        return round(float(value) * 1_000_000, 4)

    def get_minimal(self) -> dict[str, float]:
        return {
            **self.optional_field("input", self.get_per_million_tokens(self.prompt)),
            **self.optional_field("output", self.get_per_million_tokens(self.completion)),
        }


class ORArchitecture(ORBaseModel):
    modality: str | None
    input_modalities: list[InputModality]
    output_modalities: list[OutputModality]
    tokenizer: str | None = None
    instruct_type: str | None = None


class ORTopProvider(ORBaseModel):
    is_moderated: bool
    context_length: int | None = None
    max_completion_tokens: int | None = None


class ORLinks(ORBaseModel):
    details: str


class ORModelAliasTarget(ORBaseModel):
    slug: str
    name: str


class ORPerRequestLimits(ORBaseModel):
    completion_tokens: float
    prompt_tokens: float


class ORReasoning(ORBaseModel):
    mandatory: bool
    default_enabled: bool | None = None
    supported_efforts: list[str] | None = None
    default_effort: str | None = None
    supports_max_tokens: bool | None = None


class ORArtificialAnalysisBenchmarks(ORBaseModel):
    intelligence_index: float | None
    coding_index: float | None
    agentic_index: float | None


class ORDesignArenaBenchmark(ORBaseModel):
    arena: str
    category: str
    elo: float
    rank: int
    win_rate: float


class ORBenchmarks(ORBaseModel):
    design_arena: list[ORDesignArenaBenchmark]
    artificial_analysis: ORArtificialAnalysisBenchmarks | None = None


class OpenRouterModel(ORBaseModel):
    id: str
    canonical_slug: str
    name: str
    created: int  # Unix timestamp
    pricing: ORPricing
    context_length: int | None
    architecture: ORArchitecture
    top_provider: ORTopProvider
    per_request_limits: ORPerRequestLimits | None
    supported_parameters: list[str]
    default_parameters: dict[str, Any] | None
    supported_voices: list[str] | None
    links: ORLinks
    description: str | None = None
    knowledge_cutoff: str | None = None
    expiration_date: str | None = None
    hugging_face_id: str | None = None
    alias_target: ORModelAliasTarget | None = None
    benchmarks: ORBenchmarks | None = None
    reasoning: ORReasoning | None = None

    class Config:
        populate_by_name = True

    def get_url(self) -> str | None:
        if self.links.details and self.canonical_slug:
            return "https://openrouter.ai/" + self.canonical_slug.lstrip("/")
        return None

    def get_minimal_pricing(self) -> dict[str, float]:
        return self.pricing.get_minimal()

    def get_provider(self) -> str:
        return self.id.split("/")[0]

    def is_tilde_provider(self) -> bool:
        """OpenRouter router/variant listings use a leading ``~`` on the provider id."""
        return self.get_provider().startswith("~")

    def get_created_date(self) -> datetime.datetime | None:
        if self.created:
            return datetime.datetime.fromtimestamp(self.created, datetime.UTC)
        else:
            return None

    def get_cutoff_date(self) -> datetime.datetime | None:
        if self.knowledge_cutoff:
            return datetime.datetime.strptime(self.knowledge_cutoff, "%Y-%m-%d").replace(
                tzinfo=datetime.UTC
            )
        else:
            return None


class ORModelsListLinks(ORBaseModel):
    next: str | None


class OpenRouterAPIResponse(ORBaseModel):
    data: list[OpenRouterModel]
    total_count: int
    links: ORModelsListLinks
