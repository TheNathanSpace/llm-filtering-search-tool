import json
import logging

import requests

from llm_rankings.util import (
    get_env_var,
    get_intermediate_data_dir,
    setup_logging,
    validate_env_vars,
)


def form_endpoint(root: str, endpoint: str) -> str:
    """
    Forms a full URL by joining a root and an endpoint.

    :param root: The root URL.
    :param endpoint: The API endpoint.
    :return: The full URL.
    """
    endpoint = endpoint.lstrip("/")
    root = root.rstrip("/")
    url = f"{root}/{endpoint}"
    return url


def validate_response(response: requests.Response):
    """
    Validates that the API response has a 200 status code.

    :param response: The response object to validate.
    """
    if response.status_code != 200:
        raise ValueError(
            f"Failed to retrieve models from {response.url}: {response.status_code} - {response.text}"
        )


def get_artificial_analysis_models(
    aa_api_key: str, root: str = "https://artificialanalysis.ai/api/v2"
) -> dict:
    """
    Retrieves LLM models from the Artificial Analysis API.

    :param aa_api_key: The Artificial Analysis API key.
    :param root: The root URL for the Artificial Analysis API.
    :return: A dictionary containing the models data.
    """
    logging.debug("Retrieving models from Artificial Analysis")
    endpoint = "/data/llms/models"
    url = form_endpoint(root, endpoint)

    headers = {"x-api-key": aa_api_key}
    response = requests.get(url, headers=headers)
    validate_response(response)
    return response.json()


def get_openrouter_models(or_api_key: str, root: str = "https://openrouter.ai/api/v1") -> dict:
    """
    Retrieves LLM models from the OpenRouter API.

    :param or_api_key: The OpenRouter API key.
    :param root: The root URL for the OpenRouter API.
    :return: A dictionary containing the models data.
    """
    logging.debug("Retrieving models from OpenRouter")
    endpoint = "/models"
    url = form_endpoint(root, endpoint)

    headers = {"Authorization": f"Bearer {or_api_key}"}
    response = requests.get(url, headers=headers)
    validate_response(response)
    return response.json()


def write_models_data(or_models: dict, aa_models: dict):
    logging.debug("Writing raw model data to files")
    intermediate_dir = get_intermediate_data_dir()
    (intermediate_dir / "raw_or_models.json").write_text(json.dumps(or_models, indent=4))
    (intermediate_dir / "raw_aa_models.json").write_text(json.dumps(aa_models, indent=4))


def get_all_model_data() -> tuple[dict, dict]:
    """
    Retrieves LLM models from both Artificial Analysis and OpenRouter APIs.

    :return: A tuple containing dictionaries with models data from OpenRouter and Artificial Analysis.
    """
    validate_env_vars()

    aa_api_key = get_env_var("AA_API_KEY")
    or_api_key = get_env_var("OR_API_KEY")

    or_models = get_openrouter_models(or_api_key)
    aa_models = get_artificial_analysis_models(aa_api_key)

    write_models_data(or_models, aa_models)

    return or_models, aa_models


if __name__ == "__main__":
    setup_logging()
    or_models, aa_models = get_all_model_data()
    write_models_data(or_models, aa_models)
