import json
import logging

from llm_rankings import util
from llm_rankings.retrieve_data import get_all_model_data
from llm_rankings.util import get_data_dir, setup_logging


def write_models_data(or_models: list[dict], aa_models: list[dict]):
    logging.debug("Writing models data to files")
    data_dir = get_data_dir()
    (data_dir / "or_models.json").write_text(json.dumps(or_models, indent=4))
    (data_dir / "aa_models.json").write_text(json.dumps(aa_models, indent=4))


def write_unmatched_providers(or_providers: set[str], aa_providers: set[str]):
    logging.debug("Writing providers data to files")
    data_dir = get_data_dir()
    (data_dir / "unmatched_or_providers.json").write_text(
        json.dumps(sorted(or_providers), indent=4)
    )
    (data_dir / "unmatched_aa_providers.json").write_text(
        json.dumps(sorted(aa_providers), indent=4)
    )


def write_matched_providers(or_aa_providers: dict[str, str]):
    logging.debug("Writing matched providers data to files")
    data_dir = get_data_dir()
    (data_dir / "or_to_aa_providers.json").write_text(
        json.dumps(dict(sorted(or_aa_providers.items())), indent=4)
    )


def safe_delete_key(d: dict, key: str):
    if key in d:
        del d[key]


def clean_or_models(or_models: dict) -> list[dict]:
    logging.debug("Cleaning OpenRouter models")
    cleaned_models = [model for model in or_models["data"] if not model["id"].endswith(":free")]
    cleaned_models = [model for model in cleaned_models if not model["id"].startswith("~")]
    cleaned_models = [model for model in cleaned_models if not model["id"].startswith("openrouter")]
    for model in cleaned_models:
        model["created"] = util.unix_epoch_to_utc(model["created"])
        safe_delete_key(model, "per_request_limit")
        safe_delete_key(model, "default_parameters")
        safe_delete_key(model, "supported_voices")
        safe_delete_key(model, "expiration_date")
        safe_delete_key(model, "top_provider")
        safe_delete_key(model, "supported_parameters")
        safe_delete_key(model, "hugging_face_id")

        if "architecture" in model:
            if (
                "text" not in model["architecture"]["input_modalities"]
                or "text" not in model["architecture"]["output_modalities"]
            ):
                safe_delete_key(model, "architecture")

    return cleaned_models


def clean_aa_models(aa_models: dict) -> list[dict]:
    logging.debug("Cleaning Artificial Analysis models")
    cleaned_models = aa_models["data"]
    return cleaned_models


def filter_models_to_shared_providers(
    or_models: list[dict], aa_models: list[dict], matched_providers: dict[str, str]
) -> tuple[list[dict], list[dict]]:
    or_models = or_models.copy()
    aa_models = aa_models.copy()

    or_providers = matched_providers.keys()
    aa_providers = matched_providers.values()

    or_models_filtered = []
    for model in or_models:
        model_id = model["id"]
        for provider in or_providers:
            if provider in model_id:
                or_models_filtered.append(model)
                break
    aa_models_filtered = []
    for model in aa_models:
        model_provider = model["model_creator"]["name"]
        for filtered_provider in aa_providers:
            if model_provider == filtered_provider:
                aa_models_filtered.append(model)
                break

    return or_models_filtered, aa_models_filtered


def get_model_data() -> tuple[list[dict], list[dict]]:
    logging.debug("Retrieving and cleaning models data")
    aa_models, or_models = get_all_model_data()
    or_models = clean_or_models(or_models)
    aa_models = clean_aa_models(aa_models)
    return aa_models, or_models


def extract_or_providers(or_models: list[dict]) -> set[str]:
    logging.debug("Extracting OpenRouter providers")
    return {model["id"].split("/")[0] for model in or_models}


def extract_aa_providers(aa_models: list[dict]) -> set[str]:
    logging.debug("Extracting Artificial Analysis providers")
    return {model["model_creator"]["name"] for model in aa_models}


def remove_used_providers(
    matched: dict[str, str], or_providers: set[str], aa_providers: set[str]
) -> tuple[set[str], set[str]]:
    logging.debug("Removing used providers")
    new_or_providers = or_providers.copy()
    new_aa_providers = aa_providers.copy()
    new_or_providers -= set(matched.keys())
    new_aa_providers -= set(matched.values())
    return new_or_providers, new_aa_providers


def match_providers(
    or_providers: set[str], aa_providers: set[str]
) -> tuple[dict[str, str], set[str], set[str]]:
    """Returns OpenRouter -> Artificial Analysis provider mapping."""
    logging.debug("Matching providers")
    manual_mappings = {"meta-llama": "Meta", "mistralai": "Mistral", "kwaipilot": "KwaiKAT"}

    or_to_aa_map: dict[str, str] = {}

    # First, try simply matching by lowercase name
    for or_provider in or_providers:
        for aa_provider in aa_providers:
            if or_provider.lower() == aa_provider.lower():
                or_to_aa_map[or_provider] = aa_provider
                break
    or_providers, aa_providers = remove_used_providers(or_to_aa_map, or_providers, aa_providers)

    # Next, try removing dashes and spaces
    for or_provider in or_providers:
        for aa_provider in aa_providers:
            if or_provider.lower().replace("-", "").replace(" ", "") == aa_provider.lower().replace(
                "-", ""
            ).replace(" ", ""):
                or_to_aa_map[or_provider] = aa_provider
                break
    or_providers, aa_providers = remove_used_providers(or_to_aa_map, or_providers, aa_providers)

    # Next, use manual mappings
    for or_provider, aa_provider in manual_mappings.items():
        if or_provider in or_providers and aa_provider in aa_providers:
            or_to_aa_map[or_provider] = aa_provider
            or_providers.remove(or_provider)
            aa_providers.remove(aa_provider)

    return or_to_aa_map, or_providers, aa_providers


def get_and_clean_data() -> tuple[list[dict], list[dict]]:
    logging.debug("Retrieving and cleaning data")

    aa_models, or_models = get_model_data()

    or_providers = extract_or_providers(or_models)
    aa_providers = extract_aa_providers(aa_models)
    matched_providers, remaining_or_providers, remaining_aa_providers = match_providers(
        or_providers, aa_providers
    )

    or_models_filtered, aa_models_filtered = filter_models_to_shared_providers(
        or_models, aa_models, matched_providers
    )

    write_models_data(or_models_filtered, aa_models_filtered)
    write_matched_providers(matched_providers)
    write_unmatched_providers(remaining_or_providers, remaining_aa_providers)

    return or_models_filtered, aa_models_filtered


if __name__ == "__main__":
    setup_logging()
    or_models, aa_models = get_and_clean_data()
