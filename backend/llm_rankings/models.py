from typing import Any

from pydantic import BaseModel


class ORPricing(BaseModel):
    prompt: float | None = None
    completion: float | None = None
    image: float | None = None
    audio: float | None = None
    request: float | None = None
    web_search: float | None = None
    internal_reasoning: float | None = None
    input_cache_read: float | None = None
    input_cache_write: float | None = None
    audio_output: float | None = None
    image_output: float | None = None
    image_token: float | None = None
    input_audio_cache: float | None = None
    discount: float | None = None


class ORArchitecture(BaseModel):
    modality: str | None = None
    input_modalities: list[str] | None = None
    output_modalities: list[str] | None = None
    tokenizer: str | None = None
    instruct_type: str | None = None


class ORTopProvider(BaseModel):
    context_length: int | None = None
    max_completion_tokens: int | None = None
    is_moderated: bool | None = None


class ORLinks(BaseModel):
    details: str | None = None


class ORPerRequestLimits(BaseModel):
    completion_tokens: float | None = None
    prompt_tokens: float | None = None


class OpenRouterModel(BaseModel):
    id: str
    name: str | None = None
    created: int | None = None  # Raw data has unix timestamp (int)
    description: str | None = None
    context_length: int | None = None
    architecture: ORArchitecture | None = None
    pricing: ORPricing | None = None
    top_provider: ORTopProvider | None = None
    per_request_limits: ORPerRequestLimits | None = None
    supported_parameters: list[str] | None = None
    default_parameters: dict[str, Any] | None = None
    supported_voices: list[Any] | None = None
    knowledge_cutoff: str | None = None
    expiration_date: str | None = None
    links: ORLinks | None = None
    hugging_face_id: str | None = None
    canonical_slug: str | None = None

    class Config:
        populate_by_name = True
