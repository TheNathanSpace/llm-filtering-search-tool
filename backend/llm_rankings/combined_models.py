from pydantic import BaseModel, ConfigDict
from pydantic_sqlite import DataBase

from llm_rankings.or_models import InputModality, OutputModality


class CombinedModelBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CombinedModel(CombinedModelBase):
    name: str = None
    creator: str = None
    description: str | None = None
    # Milliseconds since epoch
    created: float | None = None

    url_openrouter: str | None = None
    url_artificialanalysis: str = None

    # Milliseconds since epoch
    knowledge_cutoff: float | None = None
    context_length: int | None = None

    input_modalities: list[InputModality]
    output_modalities: list[OutputModality]

    pricing_input: float | None = None
    pricing_output: float | None = None

    speed_tokens_per_second: float | None = None
    speed_time_to_first_token: float | None = None
    speed_time_to_first_answer_token: float | None = None  # Accounts for reasoning

    # Artificial Analysis evaluations (`AAEvaluations`), prefixed `benchmark_aa_`.
    benchmark_aa_artificial_analysis_intelligence_index: float | None = None
    benchmark_aa_artificial_analysis_coding_index: float | None = None
    benchmark_aa_artificial_analysis_math_index: float | None = None
    benchmark_aa_mmlu_pro: float | None = None
    benchmark_aa_gpqa: float | None = None
    benchmark_aa_hle: float | None = None
    benchmark_aa_livecodebench: float | None = None
    benchmark_aa_scicode: float | None = None
    benchmark_aa_math_500: float | None = None
    benchmark_aa_aime: float | None = None
    benchmark_aa_aime_25: float | None = None
    benchmark_aa_ifbench: float | None = None
    benchmark_aa_lcr: float | None = None
    benchmark_aa_terminalbench_hard: float | None = None
    benchmark_aa_tau2: float | None = None
    benchmark_aa_tau_banking: float | None = None
    benchmark_aa_terminalbench_v2_1: float | None = None

    # OpenRouter `ORArtificialAnalysisBenchmarks`, prefixed `benchmark_or_`.
    benchmark_or_intelligence_index: float | None = None
    benchmark_or_coding_index: float | None = None
    benchmark_or_agentic_index: float | None = None

    def add_to_database(self, db: DataBase) -> None:
        db.add("models", self, pk="name")
