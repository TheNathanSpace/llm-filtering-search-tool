import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_rankings.combined_models import CombinedModel
from llm_rankings.database import get_all_models
from llm_rankings.exfiltrate import (
    ExfiltrateResponse,
    build_exfiltrate_response,
    configured_exfiltrate_base_url,
)
from llm_rankings.refresh import (
    database_ready,
    is_refresh_in_progress,
    last_refresh_at_iso,
    refresh_if_stale,
    startup_data_load,
)
from llm_rankings.util import (
    bootstrap_env_from_argv,
    get_env_var,
    is_truthy_env,
    setup_logging,
    validate_env_vars,
)
from llm_rankings.web_enrichment import read_lifetime_cost_usd

bootstrap_env_from_argv()
setup_logging()
logger = logging.getLogger(__name__)

validate_env_vars()
frontend_port = get_env_var("FRONTEND_PORT")
backend_port = get_env_var("BACKEND_PORT")

# How often the in-process checker wakes to call refresh_if_stale (hard 24h gate).
_REFRESH_CHECK_INTERVAL_SECONDS = 60 * 60

_CLIENT_ERROR_DETAIL = "Internal server error"


def _log_background_refresh(task: asyncio.Task[object], *, label: str) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        logger.info("%s cancelled", label)
    except Exception:
        logger.exception("%s failed", label)


async def _periodic_refresh_loop() -> None:
    while True:
        await asyncio.sleep(_REFRESH_CHECK_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(refresh_if_stale, reason="scheduler")
        except Exception:
            logger.exception("Scheduled refresh check failed")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Never block serving on import/refresh (batch enrichment can take a long time).
    # Keep the previous DB online until a staging rebuild atomically replaces it.
    startup_load = asyncio.create_task(
        asyncio.to_thread(startup_data_load),
        name="startup-data-load",
    )
    startup_load.add_done_callback(
        lambda task: _log_background_refresh(task, label="Startup data load")
    )

    checker = asyncio.create_task(_periodic_refresh_loop(), name="refresh-checker")
    try:
        yield
    finally:
        # Cancel without waiting on to_thread refresh work (batch enrichment can run
        # for hours; process exit will stop the worker thread).
        startup_load.cancel()
        checker.cancel()
        await asyncio.wait(
            {startup_load, checker},
            timeout=5.0,
        )


_api_docs_enabled = is_truthy_env("ENABLE_API_DOCS")
app = FastAPI(
    title="LLM Rankings API",
    lifespan=lifespan,
    docs_url="/docs" if _api_docs_enabled else None,
    redoc_url="/redoc" if _api_docs_enabled else None,
    openapi_url="/openapi.json" if _api_docs_enabled else None,
)

origins = [
    f"http://localhost:{frontend_port}",
    f"http://localhost:{backend_port}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AppMeta(BaseModel):
    enrichment_cost_usd: float = Field(
        description="Lifetime USD spent on opt-in OpenRouter batch web enrichment"
    )
    last_refresh_at: str | None = Field(
        description="ISO-8601 UTC timestamp of the last successful model data refresh"
    )
    database_ready: bool = Field(
        description="True when the live model SQLite file exists"
    )
    refresh_in_progress: bool = Field(
        description="True while a background or CLI refresh is rebuilding the database"
    )
    exfiltrate_base_url: str | None = Field(
        description=(
            "EXFILTRATE_BASE_URL when set. Startup replaces local data from that "
            "instance, and the page warns until the process restarts without it."
        )
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/meta", response_model=AppMeta)
def get_meta():
    try:
        return AppMeta(
            enrichment_cost_usd=read_lifetime_cost_usd(),
            last_refresh_at=last_refresh_at_iso(),
            database_ready=database_ready(),
            refresh_in_progress=is_refresh_in_progress(),
            exfiltrate_base_url=configured_exfiltrate_base_url(),
        )
    except Exception as e:
        logger.exception("Failed to read app metadata")
        raise HTTPException(status_code=500, detail=_CLIENT_ERROR_DETAIL) from e


@app.get("/models", response_model=list[CombinedModel])
def get_models():
    try:
        return get_all_models()
    except Exception as e:
        logger.exception("Failed to retrieve models")
        raise HTTPException(status_code=500, detail=_CLIENT_ERROR_DETAIL) from e


@app.get("/exfiltrate", response_model=ExfiltrateResponse)
def exfiltrate():
    """Return models, provider endpoints, and durable caches for a full local restore."""
    try:
        return build_exfiltrate_response()
    except Exception as e:
        logger.exception("Failed to exfiltrate instance data")
        raise HTTPException(status_code=500, detail=_CLIENT_ERROR_DETAIL) from e


if __name__ == "__main__":
    validate_env_vars()
    host = get_env_var("BACKEND_HOST")
    port = int(get_env_var("BACKEND_PORT"))
    uvicorn.run(app, host=host, port=port)
