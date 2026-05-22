import json
import logging

import requests

from llm_rankings.util import get_data_dir, get_env_var, setup_logging, validate_env_vars


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


if __name__ == "__main__":
    setup_logging()
    validate_env_vars()
    data_dir = get_data_dir()

    aa_api_key = get_env_var("AA_API_KEY")
    or_api_key = get_env_var("OR_API_KEY")

    try:
        aa_models = get_artificial_analysis_models(aa_api_key)
        (data_dir / "aa_models.json").write_text(json.dumps(aa_models, indent=4))
    except Exception as e:
        logging.error(f"Failed to retrieve models from Artificial Analysis: {e}")

    try:
        or_models = get_openrouter_models(or_api_key)
        (data_dir / "or_models.json").write_text(json.dumps(or_models, indent=4))
    except Exception as e:
        logging.error(f"Failed to retrieve models from OpenRouter: {e}")
