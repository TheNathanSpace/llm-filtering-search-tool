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

    # List-level OR pricing left null; per-provider prices live in ``model_provider_endpoints``.
    pricing_input: float | None = None
    pricing_output: float | None = None

    # Model-level speed left null until we aggregate from ``model_provider_endpoints``.
    speed_tokens_per_second: float | None = None
    speed_time_to_first_token: float | None = None
    speed_time_to_first_answer_token: float | None = None  # Accounts for reasoning

    # OpenRouter-embedded Artificial Analysis indices (`ORArtificialAnalysisBenchmarks`).
    benchmark_or_intelligence_index: float | None = None
    benchmark_or_coding_index: float | None = None
    benchmark_or_agentic_index: float | None = None

    # models.dev + Hugging Face Hub (+ opt-in OpenRouter/Exa gap-fill for open/size/cutoff).
    is_open_weights: bool | None = None
    parameters_b: float | None = None  # Parameter count in billions (e.g. 7.0)

    def add_to_database(self, db: DataBase) -> None:
        db.add("models", self, pk="id")
