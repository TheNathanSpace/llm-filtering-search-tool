import datetime
import json
import logging
import string
from pathlib import Path

from rapidfuzz.distance.metrics_cpp import levenshtein_distance
from slugify import slugify

from llm_rankings.aa_models import ArtificialAnalysisAPIResponse
from llm_rankings.or_models import OpenRouterAPIResponse
from llm_rankings.retrieve_data import get_all_model_data
from llm_rankings.util import (
    erase_data_dir,
    get_data_dir,
    get_intermediate_data_dir,
    invert_dict,
    merge_dicts,
    safe_add_null_key,
    safe_delete_key,
    safe_rename_dict_key,
    setup_logging,
    sort_dict,
    split_to_words,
    string_is_only_in_one,
)


def write_models_data(or_models: list[dict], aa_models: list[dict], prefix: str = ""):
    logging.debug("Writing models data to files")
    intermediate_dir = get_intermediate_data_dir()
    (intermediate_dir / f"{prefix}_or_models.json").write_text(json.dumps(or_models, indent=4))
    (intermediate_dir / f"{prefix}_aa_models.json").write_text(json.dumps(aa_models, indent=4))


def write_unmatched_providers(or_providers: list[str], aa_providers: list[str]):
    logging.debug("Writing providers data to files")
    intermediate_dir = get_intermediate_data_dir()
    (intermediate_dir / "unmatched_or_providers.json").write_text(
        json.dumps(sorted(or_providers), indent=4)
    )
    (intermediate_dir / "unmatched_aa_providers.json").write_text(
        json.dumps(sorted(aa_providers), indent=4)
    )


def write_matched_providers(or_aa_providers: dict[str, str]):
    logging.debug("Writing matched providers data to files")
    (get_intermediate_data_dir() / "or_to_aa_providers.json").write_text(
        json.dumps(sort_dict(or_aa_providers), indent=4)
    )


def clean_aa_models(aa_models: dict) -> list[dict]:
    logging.debug("Cleaning Artificial Analysis models")
    cleaned_models = aa_models["data"]
    for model in cleaned_models:
        model["details"] = f"https://artificialanalysis.ai/models/{model['slug']}"
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
    or_models: OpenRouterAPIResponse
    aa_models: ArtificialAnalysisAPIResponse
    or_models, aa_models = get_all_model_data()

    cleaned_or_models = or_models.get_minimal_models()
    aa_models = clean_aa_models(aa_models)
    return cleaned_or_models, aa_models


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
) -> tuple[dict[str, str], list[str], list[str]]:
    """Returns OpenRouter -> Artificial Analysis provider mapping."""
    logging.debug("Matching providers")
    manual_mappings = {
        "meta-llama": "Meta",
        "mistralai": "Mistral",
        "kwaipilot": "KwaiKAT",
        "qwen": "Alibaba",
    }

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
        or_to_aa_map[or_provider] = aa_provider
        if or_provider in or_providers:
            or_providers.remove(or_provider)
        if aa_provider in aa_providers:
            aa_providers.remove(aa_provider)

    return or_to_aa_map, list(or_providers), list(aa_providers)


def get_models_for_provider(
    provider: str, providers_map: dict[str, str], or_models: list[dict], aa_models: list[dict]
) -> tuple[list[dict], list[dict]]:
    logging.debug(f"Getting models for provider: {provider}")
    # Get both providers
    or_provider: str = None
    aa_provider: str = None
    if provider in providers_map:
        or_provider = provider
        aa_provider = providers_map[or_provider]
    elif provider in providers_map.values():
        aa_provider = provider
        or_provider = invert_dict(providers_map)[aa_provider]
    else:
        raise ValueError(f"Provider not found in list of OR or AA providers: {provider}")

    logging.debug(f"AA provider: {aa_provider}. OR provider: {or_provider}")

    or_models_filtered = []
    aa_models_filtered = []
    for model in or_models:
        if or_provider in model["id"]:
            or_models_filtered.append(model)
    for model in aa_models:
        if aa_provider == model["model_creator"]["name"]:
            aa_models_filtered.append(model)
    return or_models_filtered, aa_models_filtered


def parse_providers(or_models: list[dict], aa_models: list[dict]) -> dict[str, str]:
    or_providers = extract_or_providers(or_models)
    aa_providers = extract_aa_providers(aa_models)
    matched_providers, remaining_or_providers, remaining_aa_providers = match_providers(
        or_providers, aa_providers
    )
    write_providers_data(matched_providers, remaining_or_providers, remaining_aa_providers)
    return matched_providers


def write_providers_data(
    matched_providers: dict[str, str],
    remaining_or_providers: list[str],
    remaining_aa_providers: list[str],
):
    write_matched_providers(matched_providers)
    write_unmatched_providers(remaining_or_providers, remaining_aa_providers)


def validate_match(model_a: str, model_b: str) -> bool:
    if string_is_only_in_one("non-instruct", model_a, model_b):
        return False
    if string_is_only_in_one("non-reasoning", model_a, model_b):
        return False
    if string_is_only_in_one("instruct", model_a, model_b):
        return False
    if string_is_only_in_one("reasoning", model_a, model_b):
        return False

    # Ensure same version
    a_words = split_to_words(model_a)
    b_words = split_to_words(model_b)
    a_ints = [int(w) for w in a_words if len(w) == 1 and w.isdigit()]
    b_ints = [int(w) for w in b_words if len(w) == 1 and w.isdigit()]
    versions_match = a_ints == b_ints
    if not versions_match:
        return False

    return True


def alphabetical_compare(a: str, b: str) -> int:
    a_words = split_to_words(a)
    b_words = split_to_words(b)

    a_alpha = " ".join(sorted(a_words))
    b_alpha = " ".join(sorted(b_words))

    return levenshtein_distance(a_alpha, b_alpha)


def match_provider_models(
    or_provider: str, aa_provider: str, or_models: list[dict], aa_models: list[dict]
) -> tuple[dict[str, str], list[str], list[str]]:
    # OR models: id google/gemini-3.5-flash -> gemini 3 5 flash
    or_models_clean_to_dirty_map: dict[str, str] = {}
    for or_model in or_models:
        or_dirty = or_model["id"]
        # Remove provider name
        or_clean = "/".join(or_dirty.split("/")[1:])
        # Remove punctuation
        or_clean = (
            or_clean.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
            .strip()
            .lower()
        )
        or_clean = or_clean.replace("thinking", "reasoning")
        # Collapse extra spaces
        or_clean = " ".join(or_clean.split())
        or_models_clean_to_dirty_map[or_clean] = or_dirty

    # AA models: slug gemini-3-5-flash -> gemini 3 5 flash
    aa_models_clean_to_dirty_map: dict[str, str] = {}
    for aa_model in aa_models:
        aa_dirty = aa_model["slug"]
        # Remove punctuation
        aa_clean = (
            aa_dirty.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
            .strip()
            .lower()
        )
        aa_clean = aa_clean.replace("thinking", "reasoning")
        # Collapse extra spaces
        aa_clean = " ".join(aa_clean.split())
        aa_models_clean_to_dirty_map[aa_clean] = aa_dirty

    remaining_or_models = list(or_models_clean_to_dirty_map.keys())
    remaining_aa_models = list(aa_models_clean_to_dirty_map.keys())

    # Pair up using Levenshtein distance
    clean_matched_models: dict[str, str] = {}
    for clean_or in remaining_or_models.copy():
        # TODO: Instead of matching with the lowest remaining,
        #  look for the actual lowest across the whole space?
        # qwen3 6 flash / qwen3 6 35b a3b : 7
        # qwen3 6 flash / qwen3 6 27b     : 7
        # qwen3 6 flash / qwen3 6 plus    : 3
        # qwen3 6 flash / qwen3 6 max     : 4
        closest_match = None
        closest_distance = float("inf")
        for clean_aa in remaining_aa_models.copy():
            if not validate_match(clean_or, clean_aa):
                continue
            distance = alphabetical_compare(clean_or, clean_aa)
            if clean_or == "qwen3 6 flash":
                logging.debug(f"{clean_or} / {clean_aa} : {distance}")
            if distance < closest_distance and distance <= 4:
                closest_distance = distance
                closest_match = clean_aa

        if closest_match:
            clean_matched_models[clean_or] = closest_match
            remaining_or_models.remove(clean_or)
            remaining_aa_models.remove(closest_match)

    dirty_matched_models: dict[str, str] = {}
    for clean_or, clean_aa in clean_matched_models.items():
        dirty_matched_models[or_models_clean_to_dirty_map[clean_or]] = aa_models_clean_to_dirty_map[
            clean_aa
        ]

    dirty_remaining_or_models = [or_models_clean_to_dirty_map[m] for m in remaining_or_models]
    dirty_remaining_aa_models = [aa_models_clean_to_dirty_map[m] for m in remaining_aa_models]

    return (
        sort_dict(dirty_matched_models),
        sorted(dirty_remaining_or_models),
        sorted(dirty_remaining_aa_models),
    )


def create_provider_dir(or_provider: str) -> Path:
    intermediate_dir = get_intermediate_data_dir()
    provider_slug = slugify(or_provider)
    provider_dir = intermediate_dir / provider_slug
    provider_dir.mkdir(parents=True, exist_ok=True)
    return provider_dir


def write_matched_models(or_provider: str, matched_models: dict):
    logging.debug(f"Writing matched models for provider {or_provider} to file")
    provider_dir = create_provider_dir(or_provider)
    (provider_dir / "matched_models.json").write_text(json.dumps(matched_models, indent=4))


def write_unmatched_models(or_provider: str, or_models: list[dict], aa_models: list[dict]):
    logging.debug(f"Writing unmatched models for provider {or_provider} to file")
    provider_dir = create_provider_dir(or_provider)
    (provider_dir / "unmatched_models_or.json").write_text(json.dumps(or_models, indent=4))
    (provider_dir / "unmatched_models_aa.json").write_text(json.dumps(aa_models, indent=4))


def process_provider(
    or_provider: str,
    aa_provider: str,
    matched_providers: dict[str, str],
    or_models_filtered: list[dict],
    aa_models_filtered: list[dict],
) -> dict[str, str]:
    or_models_for_provider, aa_models_for_provider = get_models_for_provider(
        or_provider, matched_providers, or_models_filtered, aa_models_filtered
    )
    write_unmatched_models(or_provider, or_models_for_provider, aa_models_for_provider)

    matched_models, remaining_or_models, remaining_aa_models = match_provider_models(
        or_provider, aa_provider, or_models_for_provider, aa_models_for_provider
    )
    provider_dict = {
        "or_to_aa_models": matched_models,
        "unmatched_or_models": remaining_or_models,
        "unmatched_aa_models": remaining_aa_models,
    }
    write_matched_models(or_provider, provider_dict)

    return matched_models


def find_model(model_name: str, models: list[dict], is_aa=False) -> dict:
    key = "slug" if is_aa else "id"
    for model in models:
        if model[key] == model_name:
            return model
    raise ValueError(f"Model not found: {model_name}")


def generisize_aa_model(aa_model: dict) -> dict:
    generisized_model = aa_model.copy()
    safe_delete_key(generisized_model, "id")
    safe_delete_key(generisized_model, "slug")
    safe_rename_dict_key(generisized_model, "release_date", "aa_release_date")
    if "model_creator" in generisized_model and "name" in generisized_model["model_creator"]:
        generisized_model["creator"] = generisized_model["model_creator"]["name"]
        del generisized_model["model_creator"]
    generisized_model["speed"]: dict[str, float] = {}
    for key in [
        "median_output_tokens_per_second",
        "median_time_to_first_token_seconds",
        "median_time_to_first_answer_token",
    ]:
        generisized_model["speed"][key] = generisized_model[key]
        del generisized_model[key]
    if "details" in generisized_model:
        generisized_model["urls"] = {"aa_url": generisized_model["details"]}
        del generisized_model["details"]
    if "pricing" in generisized_model:
        safe_delete_key(generisized_model["pricing"], "price_1m_blended_3_to_1")
        safe_rename_dict_key(generisized_model["pricing"], "price_1m_output_tokens", "output")
        safe_rename_dict_key(generisized_model["pricing"], "price_1m_input_tokens", "input")
    safe_rename_dict_key(generisized_model, "pricing", "aa_pricing")
    return generisized_model


def generisize_or_model(or_model: dict) -> dict:
    generisized_model = or_model.copy()
    safe_delete_key(generisized_model, "id")
    safe_delete_key(generisized_model, "canonical_slug")
    safe_rename_dict_key(generisized_model, "created", "or_created")
    if "details" in generisized_model:
        generisized_model["urls"] = {"or_url": generisized_model["details"]}
        safe_delete_key(generisized_model, "details")
    if "pricing" in generisized_model:
        safe_rename_dict_key(generisized_model["pricing"], "prompt", "input")
        safe_rename_dict_key(generisized_model["pricing"], "completion", "output")
    safe_rename_dict_key(generisized_model, "pricing", "or_pricing")
    safe_add_null_key(generisized_model, "knowledge_cutoff")
    return generisized_model


def combine_or_aa_models(
    matched_models: dict[str, str], or_models: list[dict], aa_models: list[dict]
) -> list[dict]:
    combined_models: list[dict] = []
    for or_name, aa_name in matched_models.items():
        or_model = find_model(or_name, or_models, is_aa=False)
        aa_model = find_model(aa_name, aa_models, is_aa=True)
        or_model = generisize_or_model(or_model)
        aa_model = generisize_aa_model(aa_model)
        merged_model = merge_dicts(or_model, aa_model)

        # Use earliest release date
        if "or_created" in merged_model and "aa_release_date" in merged_model:
            or_created: datetime.datetime = datetime.datetime.fromisoformat(or_model["or_created"])
            aa_created: datetime.datetime = datetime.datetime.strptime(
                aa_model["aa_release_date"], "%Y-%m-%d"
            ).replace(tzinfo=datetime.UTC)
            earliest = min(or_created, aa_created)
            merged_model["created"] = earliest.strftime("%Y-%m-%d")
            safe_delete_key(merged_model, "or_created")
            safe_delete_key(merged_model, "aa_release_date")
        elif "or_created" in merged_model:
            or_created: datetime.datetime = datetime.datetime.fromisoformat(or_model["or_created"])
            merged_model["created"] = or_created.strftime("%Y-%m-%d")
            safe_delete_key(merged_model, "created")
        elif "aa_release_date" in merged_model:
            aa_created: datetime.datetime = datetime.datetime.strptime(
                aa_model["aa_release_date"], "%Y-%m-%d"
            ).replace(tzinfo=datetime.UTC)
            merged_model["created"] = aa_created.strftime("%Y-%m-%d")
            safe_delete_key(merged_model, "aa_release_date")

        # Fallback to AA pricing if OR does not exist
        if "or_pricing" in merged_model:
            safe_rename_dict_key(merged_model, "or_pricing", "pricing")
            safe_delete_key(merged_model, "aa_pricing")
        elif "aa_pricing" in merged_model:
            safe_rename_dict_key(merged_model, "aa_pricing", "pricing")

        combined_models.append(sort_dict(merged_model))
    return combined_models


def write_combined_models(combined_models: list[dict]):
    combined_models_path = get_data_dir() / "combined_models.json"
    combined_models_path.write_text(json.dumps(combined_models, indent=4))
    logging.info(f"Combined models written to {combined_models_path}")


def get_and_clean_data() -> tuple[list[dict], list[dict]]:
    logging.debug("Retrieving and cleaning data")

    or_models, aa_models = get_model_data()
    write_models_data(or_models, aa_models, "cleaned")

    matched_providers = parse_providers(or_models, aa_models)

    or_models_filtered, aa_models_filtered = filter_models_to_shared_providers(
        or_models, aa_models, matched_providers
    )
    write_models_data(or_models_filtered, aa_models_filtered, "filtered")

    all_matched_models: dict[str, str] = {}
    for or_provider, aa_provider in matched_providers.items():
        matched_models = process_provider(
            or_provider, aa_provider, matched_providers, or_models_filtered, aa_models_filtered
        )
        all_matched_models.update(matched_models)

    combined_models = combine_or_aa_models(
        all_matched_models, or_models_filtered, aa_models_filtered
    )
    write_combined_models(combined_models)

    return combined_models


if __name__ == "__main__":
    setup_logging("DEBUG")
    erase_data_dir()
    combined_models = get_and_clean_data()
