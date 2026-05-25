from pydantic import BaseModel, ConfigDict
from pydantic_sqlite import DataBase


class CombinedModelBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CombinedModel(CombinedModelBase):
    name: str = None
    creator: str = None
    description: str | None = None
    created: str | None = None

    url_openrouter: str | None = None
    url_artificialanalysis: str = None

    knowledge_cutoff: str | None = None
    context_length: int | None = None

    pricing_input: float | None = None
    pricing_output: float | None = None

    speed_tokens_per_second: float | None = None
    speed_time_to_first_token: float | None = None
    speed_time_to_first_answer_token: float | None = None  # Accounts for reasoning

    benchmark_artificial_analysis_intelligence_index: float | None = None
    benchmark_artificial_analysis_coding_index: float | None = None
    benchmark_artificial_analysis_math_index: float | None = None
    benchmark_mmlu_pro: float | None = None
    benchmark_gpqa: float | None = None
    benchmark_hle: float | None = None
    benchmark_livecodebench: float | None = None
    benchmark_scicode: float | None = None
    benchmark_math_500: float | None = None
    benchmark_aime: float | None = None
    benchmark_aime_25: float | None = None
    benchmark_ifbench: float | None = None
    benchmark_lcr: float | None = None
    benchmark_terminalbench_hard: float | None = None
    benchmark_tau2: float | None = None

    def add_to_database(self, db: DataBase) -> None:
        db.add("models", self, pk="name")
