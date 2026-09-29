import importlib
import json
import logging
from pathlib import Path

from pydantic_sqlite import DataBase
from pydantic_sqlite._core import TableBaseModel

from llm_rankings.clean_data import get_and_clean_data
from llm_rankings.combined_models import CombinedModel
from llm_rankings.provider_endpoints import ModelProviderEndpoint
from llm_rankings.util import get_data_dir

logger = logging.getLogger(__name__)


def get_database_path() -> Path:
    return get_data_dir() / "database.db"


def initialize_database() -> DataBase:
    logger.debug(f"Initializing database at {get_database_path().as_posix()}")
    already_exists = get_database_path().exists()
    db = DataBase(filename_or_conn=get_database_path())

    if already_exists:
        # Annoying workarounds for https://github.com/Phil997/pydantic-sqlite/issues/36
        table_names = [
            n[0]
            for n in db._db.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        ]
        logger.debug(f"Database tables: {table_names}")
        base_models = db._db.execute(
            'SELECT "table", modulename, pks FROM __basemodels__;'
        ).fetchall()
        for base_model in base_models:
            table: str = base_model[0]
            modulename: str = base_model[1]
            pks: list[str] = json.loads(base_model[2])

            classname = modulename.split(".")[-1]
            modulename = ".".join(modulename.split(".")[:-1])
            my_module = importlib.import_module(modulename)

            db._primary_keys[table] = pks[0]

            tablebasemodel = TableBaseModel(
                table=table, basemodel_cls=getattr(my_module, classname), pks=pks
            )
            db._basemodels[table] = tablebasemodel

    return db


def wipe_database():
    logger.debug(f"Wiping database at {get_database_path().as_posix()}")
    Path.unlink(get_database_path(), missing_ok=True)


def populate_with_models():
    models, provider_endpoints = get_and_clean_data()
    db: DataBase = initialize_database()
    logger.debug(f"Writing {len(models)} models to database")
    for model in models:
        model.add_to_database(db)
    logger.debug(f"Wrote {len(models)} models to database")
    logger.debug(f"Writing {len(provider_endpoints)} provider endpoints to database")
    for row in provider_endpoints:
        row.add_to_database(db)
    logger.debug(f"Wrote {len(provider_endpoints)} provider endpoints to database")


def get_all_models() -> list[CombinedModel]:
    db: DataBase = initialize_database()
    models: list[CombinedModel] = list(db("models"))
    return models


def get_all_provider_endpoints() -> list[ModelProviderEndpoint]:
    db: DataBase = initialize_database()
    return list(db("model_provider_endpoints"))


if __name__ == "__main__":
    # Prefer: python -m llm_rankings.refresh [--force] [--source …]
    from llm_rankings.refresh import main as refresh_main

    raise SystemExit(refresh_main())
