import json
import logging

import requests

from llm_rankings.or_models import OpenRouterAPIResponse
from llm_rankings.util import (
    bootstrap_env_from_argv,
    get_env_var,
    get_raw_data_dir,
    setup_logging,
    validate_env_vars,
)

logger = logging.getLogger(__name__)


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


def get_openrouter_models(
    or_api_key: str, root: str = "https://openrouter.ai/api/v1"
) -> OpenRouterAPIResponse:
    """
    Retrieves LLM models from the OpenRouter API.

    :param or_api_key: The OpenRouter API key.
    :param root: The root URL for the OpenRouter API.
    :return: A dictionary containing the models data.
    """
    logger.debug("Retrieving models from OpenRouter")
    endpoint = "/models"
    url = form_endpoint(root, endpoint)

    headers = {"Authorization": f"Bearer {or_api_key}"}
    response = requests.get(url, headers=headers)
    validate_response(response)
    response_json = response.json()
    try:
        model = OpenRouterAPIResponse.model_validate(response_json)
    except Exception:
        logger.error(f"Failed to validate OpenRouter response: {response_json}")
        raw = get_raw_data_dir() / "or_response.json"
        logger.debug(f"Writing raw response to {raw.as_posix()}")
        raw.write_text(json.dumps(response_json, indent=4))
        exit(-1)
    return model


def write_models_data(or_models: OpenRouterAPIResponse):
    logger.debug("Writing raw model data to files")
    raw = get_raw_data_dir()
    (raw / "raw_or_models.json").write_text(json.dumps(or_models.model_dump(), indent=4))


def get_all_model_data() -> OpenRouterAPIResponse:
    """
    Retrieves LLM models from OpenRouter.

    :return: Parsed OpenRouter models list response.
    """
    validate_env_vars()

    or_api_key = get_env_var("OR_API_KEY")
    or_models: OpenRouterAPIResponse = get_openrouter_models(or_api_key)
    write_models_data(or_models)
    return or_models


if __name__ == "__main__":
    bootstrap_env_from_argv()
    setup_logging()
    get_all_model_data()
