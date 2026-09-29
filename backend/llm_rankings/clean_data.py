import json
import logging

from llm_rankings.combined_models import CombinedModel
from llm_rankings.hf_enrichment import parameters_b_for_repo_ids
from llm_rankings.models_dev import open_weights_by_openrouter_id
from llm_rankings.or_endpoints import ORListEndpointsData
from llm_rankings.or_models import OpenRouterAPIResponse, OpenRouterModel
from llm_rankings.provider_endpoints import ModelProviderEndpoint, from_or_public_endpoint
from llm_rankings.retrieve_data import get_all_model_data, get_endpoints_for_models
from llm_rankings.util import (
    bootstrap_env_from_argv,
    erase_data_dir,
    get_data_dir,
    setup_logging,
)
from llm_rankings.web_enrichment import enrich_combined_models

logger = logging.getLogger(__name__)


def _prefixed_scores(prefix: str, values: dict[str, object]) -> dict[str, float]:
    return {f"{prefix}{key}": round(float(value), 4) for key, value in values.items()}


def openrouter_to_combined(
    or_model: OpenRouterModel,
    *,
    open_weights: dict[str, bool],
    parameters_b: dict[str, float | None],
) -> CombinedModel:
    created = or_model.get_created_date()
    cutoff = or_model.get_cutoff_date()
    or_benchmarks = (
        or_model.benchmarks.artificial_analysis.model_dump(exclude_none=True, by_alias=False)
        if or_model.benchmarks and or_model.benchmarks.artificial_analysis
        else {}
    )
    hf_id = (or_model.hugging_face_id or "").strip() or None
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
        # List-level OR pricing omitted — use ``model_provider_endpoints`` instead.
        pricing_input=None,
        pricing_output=None,
        # Model-level speed_* still null until we choose an aggregation from providers.
        is_open_weights=open_weights.get(or_model.id),
        parameters_b=parameters_b.get(hf_id) if hf_id else None,
        **_prefixed_scores("benchmark_or_", or_benchmarks),
    )


def combine_openrouter_models(or_models: OpenRouterAPIResponse) -> list[CombinedModel]:
    kept: list[OpenRouterModel] = []
    skipped_tilde = 0
    skipped_free = 0
    for model in or_models.data:
        if model.is_tilde_provider():
            skipped_tilde += 1
            continue
        if model.is_free_variant():
            skipped_free += 1
            continue
        kept.append(model)
    if skipped_tilde:
        logger.info(
            "Skipping %s OpenRouter model(s) with '~' provider ids (router/variant listings)",
            skipped_tilde,
        )
    if skipped_free:
        logger.info(
            "Skipping %s OpenRouter free model(s) (ids ending in ':free')",
            skipped_free,
        )
    open_weights = open_weights_by_openrouter_id()
    hf_ids = {
        (model.hugging_face_id or "").strip() for model in kept if (model.hugging_face_id or "").strip()
    }
    parameters_b = parameters_b_for_repo_ids(hf_ids)
    combined = [
        openrouter_to_combined(model, open_weights=open_weights, parameters_b=parameters_b)
        for model in kept
    ]
    # Opt-in OpenRouter chat + Exa gap-fill for missing open-weights / size.
    enrich_combined_models(combined)
    return combined


def combine_provider_endpoints(
    endpoint_lists: list[ORListEndpointsData],
    *,
    kept_model_ids: set[str],
) -> list[ModelProviderEndpoint]:
    """Flatten OR endpoint payloads into DB rows for kept catalog model ids."""
    rows: list[ModelProviderEndpoint] = []
    for payload in endpoint_lists:
        model_id = payload.id
        if model_id not in kept_model_ids:
            continue
        for endpoint in payload.endpoints:
            rows.append(from_or_public_endpoint(endpoint, model_id=model_id))
    logger.info("Combined %d provider endpoint rows", len(rows))
    return rows


def write_combined_models(combined_models: list[CombinedModel]):
    combined_models_path = get_data_dir() / "combined_models.json"
    serialized = [m.model_dump() for m in combined_models]
    combined_models_path.write_text(json.dumps(serialized, indent=4))
    logger.info(f"Combined models written to {combined_models_path}")


def write_provider_endpoints(rows: list[ModelProviderEndpoint]) -> None:
    path = get_data_dir() / "model_provider_endpoints.json"
    path.write_text(json.dumps([r.model_dump() for r in rows], indent=4))
    logger.info("Provider endpoints written to %s (%d rows)", path.as_posix(), len(rows))


def get_and_clean_data() -> tuple[list[CombinedModel], list[ModelProviderEndpoint]]:
    logger.info("Refresh pipeline: fetching OpenRouter model catalog")
    or_models = get_all_model_data()
    logger.info(
        "Refresh pipeline: combining models (models.dev + Hugging Face + optional web enrichment)"
    )
    combined_models = combine_openrouter_models(or_models)
    kept_ids = {m.id for m in combined_models}
    kept_or_models = [m for m in or_models.data if m.id in kept_ids]
    logger.info(
        "Refresh pipeline: fetching OpenRouter endpoints for %d models",
        len(kept_or_models),
    )
    endpoint_lists = get_endpoints_for_models(kept_or_models)
    provider_rows = combine_provider_endpoints(endpoint_lists, kept_model_ids=kept_ids)
    write_combined_models(combined_models)
    write_provider_endpoints(provider_rows)
    logger.info("Refresh pipeline: done (%d models, %d provider rows)", len(combined_models), len(provider_rows))
    return combined_models, provider_rows


if __name__ == "__main__":
    bootstrap_env_from_argv()
    setup_logging()
    erase_data_dir()
    get_and_clean_data()
