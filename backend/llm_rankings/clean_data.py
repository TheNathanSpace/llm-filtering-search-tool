import json
import logging

from llm_rankings.combined_models import CombinedModel
from llm_rankings.or_models import OpenRouterAPIResponse, OpenRouterModel
from llm_rankings.retrieve_data import get_all_model_data
from llm_rankings.util import (
    bootstrap_env_from_argv,
    erase_data_dir,
    get_data_dir,
    setup_logging,
)

logger = logging.getLogger(__name__)


def _prefixed_scores(prefix: str, values: dict[str, object]) -> dict[str, float]:
    return {f"{prefix}{key}": round(float(value), 4) for key, value in values.items()}


def openrouter_to_combined(or_model: OpenRouterModel) -> CombinedModel:
    created = or_model.get_created_date()
    cutoff = or_model.get_cutoff_date()
    pricing = or_model.get_minimal_pricing()
    or_benchmarks = (
        or_model.benchmarks.artificial_analysis.model_dump(exclude_none=True, by_alias=False)
        if or_model.benchmarks and or_model.benchmarks.artificial_analysis
        else {}
    )
    return CombinedModel(
        id=or_model.id,
        name=or_model.name,
        creator=or_model.get_provider(),
        description=or_model.description,
        created=(created.timestamp() * 1000) if created else None,
        url_openrouter=or_model.get_url(),
        knowledge_cutoff=(cutoff.timestamp() * 1000) if cutoff else None,
        context_length=or_model.context_length,
        input_modalities=or_model.architecture.input_modalities,
        output_modalities=or_model.architecture.output_modalities,
        pricing_input=pricing.get("input"),
        pricing_output=pricing.get("output"),
        # speed_* left null — see CombinedModel.
        **_prefixed_scores("benchmark_or_", or_benchmarks),
    )


def combine_openrouter_models(or_models: OpenRouterAPIResponse) -> list[CombinedModel]:
    return [openrouter_to_combined(model) for model in or_models.data]


def write_combined_models(combined_models: list[CombinedModel]):
    combined_models_path = get_data_dir() / "combined_models.json"
    serialized = [m.model_dump() for m in combined_models]
    combined_models_path.write_text(json.dumps(serialized, indent=4))
    logger.info(f"Combined models written to {combined_models_path}")


def get_and_clean_data() -> list[CombinedModel]:
    logger.debug("Retrieving and cleaning data")
    or_models = get_all_model_data()
    combined_models = combine_openrouter_models(or_models)
    write_combined_models(combined_models)
    return combined_models


if __name__ == "__main__":
    bootstrap_env_from_argv()
    setup_logging()
    erase_data_dir()
    get_and_clean_data()
