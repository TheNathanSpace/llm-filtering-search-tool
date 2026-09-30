from pydantic import BaseModel, ConfigDict
from pydantic_sqlite import DataBase

from llm_rankings.or_models import InputModality, OutputModality


class CombinedModelBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CombinedModel(CombinedModelBase):
    id: str  # OpenRouter model id (e.g. "openai/gpt-4o")
    name: str = None
    creator: str = None
    description: str | None = None
    # Milliseconds since epoch
    created: float | None = None

    url_openrouter: str | None = None

    # Milliseconds since epoch
    knowledge_cutoff: float | None = None
    context_length: int | None = None

    input_modalities: list[InputModality]
    output_modalities: list[OutputModality]

    # Listed $/1M from the provider chosen in ``provider_choice`` (null when none are priced).
    pricing_input: float | None = None
    pricing_output: float | None = None
    selected_provider: str | None = None

    # Median speed for that same provider (OpenRouter last-30m p50).
    throughput: float | None = None  # output tokens/sec
    latency_ms: float | None = None  # time to first token

    # OpenRouter-embedded Artificial Analysis indices (`ORArtificialAnalysisBenchmarks`).
    benchmark_or_intelligence_index: float | None = None
    benchmark_or_coding_index: float | None = None
    benchmark_or_agentic_index: float | None = None

    # models.dev + Hugging Face Hub (+ opt-in OpenRouter/Exa gap-fill for open/size/cutoff).
    is_open_weights: bool | None = None
    parameters_b: float | None = None  # Parameter count in billions (e.g. 7.0)

    def add_to_database(self, db: DataBase) -> None:
        db.add("models", self, pk="id")
