from pydantic import BaseModel, ConfigDict

# https://artificialanalysis.ai/api-reference/#models-endpoint


class AABaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AACreator(AABaseModel):
    id: str
    name: str
    slug: str


class AAEvaluations(AABaseModel):
    artificial_analysis_intelligence_index: float | None = None
    artificial_analysis_coding_index: float | None = None
    artificial_analysis_math_index: float | None = None
    mmlu_pro: float | None = None
    gpqa: float | None = None
    hle: float | None = None
    livecodebench: float | None = None
    scicode: float | None = None
    math_500: float | None = None
    aime: float | None = None
    aime_25: float | None = None
    ifbench: float | None = None
    lcr: float | None = None
    terminalbench_hard: float | None = None
    tau2: float | None = None


class AAPricing(AABaseModel):
    price_1m_blended_3_to_1: float | None = None
    price_1m_input_tokens: float | None = None
    price_1m_output_tokens: float | None = None


class AAPromptOptions(AABaseModel):
    parallel_queries: int | None = None
    prompt_length: str | int | None = None


class AAModel(AABaseModel):
    id: str
    name: str
    slug: str
    release_date: str | None = None
    model_creator: AACreator
    evaluations: AAEvaluations | None = None
    pricing: AAPricing | None = None
    median_output_tokens_per_second: float | None = None
    median_time_to_first_token_seconds: float | None = None
    median_time_to_first_answer_token: float | None = None


class ArtificialAnalysisAPIResponse(AABaseModel):
    status: int
    prompt_options: AAPromptOptions | None = None
    data: list[AAModel]
