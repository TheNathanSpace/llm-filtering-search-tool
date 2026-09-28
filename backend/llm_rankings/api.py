import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from llm_rankings.combined_models import CombinedModel
from llm_rankings.database import (
    get_all_models,
    get_database_path,
    populate_with_models,
    wipe_database,
)
from llm_rankings.util import bootstrap_env_from_argv, get_env_var, setup_logging, validate_env_vars

bootstrap_env_from_argv()
setup_logging()
logger = logging.getLogger(__name__)

validate_env_vars()
frontend_port = get_env_var("FRONTEND_PORT")
backend_port = get_env_var("BACKEND_PORT")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if not get_database_path().exists():
        logger.info("Database not found; fetching model data from APIs...")
        populate_with_models()
        logger.info("Database seeded successfully.")
    yield


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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/refresh")
def refresh_data():
    try:
        logger.info("Refreshing data from APIs...")
        wipe_database()
        populate_with_models()

        logger.info("Data refreshed successfully.")
        return {"message": "Data refreshed successfully"}
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
