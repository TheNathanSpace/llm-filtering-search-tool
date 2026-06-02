import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from llm_rankings.combined_models import CombinedModel
from llm_rankings.database import get_all_models, populate_with_models, wipe_database
from llm_rankings.util import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Rankings API")

origins = [
    "http://localhost:3030",
    "http://localhost:8000",
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
