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
from llm_rankings.refresh import last_refresh_at_iso, refresh_if_stale
from llm_rankings.util import bootstrap_env_from_argv, get_env_var, setup_logging, validate_env_vars
from llm_rankings.web_enrichment import read_lifetime_cost_usd

bootstrap_env_from_argv()
setup_logging()
logger = logging.getLogger(__name__)

validate_env_vars()
frontend_port = get_env_var("FRONTEND_PORT")
backend_port = get_env_var("BACKEND_PORT")

# How often the in-process checker wakes to call refresh_if_stale (hard 24h gate).
_REFRESH_CHECK_INTERVAL_SECONDS = 60 * 60


async def _periodic_refresh_loop() -> None:
    while True:
        await asyncio.sleep(_REFRESH_CHECK_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(refresh_if_stale, reason="scheduler")
        except Exception:
            logger.exception("Scheduled refresh check failed")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        await asyncio.to_thread(refresh_if_stale, reason="startup")
    except Exception:
        logger.exception("Startup refresh failed")
        raise

    checker = asyncio.create_task(_periodic_refresh_loop(), name="refresh-checker")
    try:
        yield
    finally:
        checker.cancel()
        try:
            await checker
        except asyncio.CancelledError:
            pass


app = FastAPI(title="LLM Rankings API", lifespan=lifespan)

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
        description="Lifetime USD spent on opt-in OpenRouter/Exa web enrichment"
    )
    last_refresh_at: str | None = Field(
        description="ISO-8601 UTC timestamp of the last successful model data refresh"
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
        )
    except Exception as e:
        logger.exception("Failed to read app metadata")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/refresh")
def refresh_data():
    try:
        result = refresh_if_stale(reason="api")
        return result.as_api_dict()
    except Exception as e:
        logger.exception("Failed to refresh data")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/models", response_model=list[CombinedModel])
def get_models():
    try:
        return get_all_models()
    except Exception as e:
        logger.exception("Failed to retrieve models")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    validate_env_vars()
    host = get_env_var("BACKEND_HOST")
    port = int(get_env_var("BACKEND_PORT"))
    uvicorn.run(app, host=host, port=port)
