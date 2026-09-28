import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from llm_rankings.or_endpoints import (
    OREndpointsAPIResponse,
    ORListEndpointsData,
    endpoints_path_for_model,
)
from llm_rankings.or_models import OpenRouterAPIResponse, OpenRouterModel
from llm_rankings.util import (
    bootstrap_env_from_argv,
    get_env_var,
    get_raw_data_dir,
    setup_logging,
    validate_env_vars,
)

logger = logging.getLogger(__name__)

OR_API_ROOT = "https://openrouter.ai/api/v1"
# Polite concurrent fetch of per-model endpoints (metadata GETs; not inference).
ENDPOINTS_MAX_WORKERS = 8
ENDPOINTS_MAX_RETRIES = 4
ENDPOINTS_INITIAL_BACKOFF_SECONDS = 1.0
ENDPOINTS_TIMEOUT_SECONDS = 30


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
    or_api_key: str, root: str = OR_API_ROOT
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


def _fetch_one_model_endpoints(
    session: requests.Session,
    model_id: str,
    root: str,
) -> ORListEndpointsData:
    """
    GET endpoints for one model with retries on 429 / transient errors.
    """
    url = form_endpoint(root, endpoints_path_for_model(model_id))
    backoff = ENDPOINTS_INITIAL_BACKOFF_SECONDS

    for attempt in range(1, ENDPOINTS_MAX_RETRIES + 1):
        try:
            response = session.get(url, timeout=ENDPOINTS_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            logger.warning(
                "OpenRouter endpoints request error for %s (attempt %d/%d): %s",
                model_id,
                attempt,
                ENDPOINTS_MAX_RETRIES,
                exc,
            )
            if attempt == ENDPOINTS_MAX_RETRIES:
                raise
            time.sleep(backoff)
            backoff *= 2
            continue

        if response.status_code == 200:
            parsed = OREndpointsAPIResponse.model_validate(response.json())
            return parsed.data

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait = (
                float(retry_after)
                if retry_after is not None and retry_after.replace(".", "", 1).isdigit()
                else backoff
            )
            logger.warning(
                "OpenRouter rate-limited endpoints for %s; sleeping %.1fs (attempt %d/%d)",
                model_id,
                wait,
                attempt,
                ENDPOINTS_MAX_RETRIES,
            )
            time.sleep(wait)
            backoff *= 2
            continue

        if response.status_code in {500, 502, 503, 504} and attempt < ENDPOINTS_MAX_RETRIES:
            logger.warning(
                "OpenRouter endpoints %s for %s; retrying in %.1fs (attempt %d/%d)",
                response.status_code,
                model_id,
                backoff,
                attempt,
                ENDPOINTS_MAX_RETRIES,
            )
            time.sleep(backoff)
            backoff *= 2
            continue

        raise ValueError(
            f"Failed to retrieve endpoints for {model_id} from {response.url}: "
            f"{response.status_code} - {response.text[:300]}"
        )

    raise ValueError(f"Exhausted retries fetching endpoints for {model_id}")


def get_openrouter_endpoints(
    model_ids: list[str],
    or_api_key: str,
    root: str = OR_API_ROOT,
    *,
    max_workers: int = ENDPOINTS_MAX_WORKERS,
) -> list[ORListEndpointsData]:
    """
    Fetch per-provider endpoint metadata for each model id.

    Uses a bounded thread pool and retries 429 / 5xx with backoff.
    Failures for individual models are logged and skipped so one 404 does not
    abort the whole refresh.
    """
    ids = sorted({mid for mid in model_ids if mid})
    if not ids:
        return []

    logger.info(
        "Retrieving OpenRouter endpoints for %d models (max_workers=%d)",
        len(ids),
        max_workers,
    )
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {or_api_key}"})

    results: list[ORListEndpointsData] = []
    failures = 0
    done = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_one_model_endpoints, session, model_id, root): model_id
            for model_id in ids
        }
        for future in as_completed(futures):
            model_id = futures[future]
            done += 1
            try:
                results.append(future.result())
            except Exception:
                failures += 1
                logger.exception("Skipping endpoints for %s", model_id)
            if done % 50 == 0 or done == len(ids):
                logger.info(
                    "OpenRouter endpoints progress: %d/%d (%d failed)",
                    done,
                    len(ids),
                    failures,
                )

    session.close()
    logger.info(
        "Retrieved endpoints for %d/%d models (%d failed)",
        len(results),
        len(ids),
        failures,
    )
    return results


def write_endpoints_data(endpoints: list[ORListEndpointsData]) -> None:
    logger.debug("Writing raw OpenRouter endpoints data")
    raw = get_raw_data_dir()
    payload = [item.model_dump() for item in endpoints]
    (raw / "raw_or_endpoints.json").write_text(json.dumps(payload, indent=4))


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


def get_endpoints_for_models(or_models: list[OpenRouterModel]) -> list[ORListEndpointsData]:
    """Fetch and persist raw endpoints for the given catalog models."""
    validate_env_vars()
    or_api_key = get_env_var("OR_API_KEY")
    model_ids = [m.id for m in or_models]
    endpoints = get_openrouter_endpoints(model_ids, or_api_key)
    write_endpoints_data(endpoints)
    return endpoints


if __name__ == "__main__":
    bootstrap_env_from_argv()
    setup_logging()
    get_all_model_data()
