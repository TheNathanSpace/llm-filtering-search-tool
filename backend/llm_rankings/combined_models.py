from pydantic import BaseModel, ConfigDict

from llm_rankings.aa_models import AAEvaluations


class CombinedModelBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CombinedPricing(CombinedModelBase):
    input: float | None = None
    output: float | None = None


class CombinedSpeed(CombinedModelBase):
    tokens_per_second: float | None = None
    time_to_first_token: float | None = None
    time_to_first_answer_token: float | None = None  # Accounts for reasoning


class CombinedUrls(CombinedModelBase):
    or_url: str | None = None
    aa_url: str | None = None


class CombinedModel(CombinedModelBase):
    name: str | None = None
    description: str | None = None
    created: str | None = None
    creator: str | None = None
    urls: CombinedUrls | None = None
    knowledge_cutoff: str | None = None
    context_length: int | None = None
    evaluations: AAEvaluations | None = None
    pricing: CombinedPricing | None = None
    speed: CombinedSpeed | None = None
