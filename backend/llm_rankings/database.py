import importlib
import json
import logging
import os
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


def get_staging_database_path() -> Path:
    """Temporary SQLite path used while a refresh rebuilds; live DB stays readable."""
    return get_data_dir() / "database.db.staging"


def initialize_database(path: Path | None = None) -> DataBase:
    db_path = path if path is not None else get_database_path()
    logger.debug(f"Initializing database at {db_path.as_posix()}")
    already_exists = db_path.exists()
    db = DataBase(filename_or_conn=db_path)

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


def _close_database(db: DataBase) -> None:
    connection = getattr(db, "_db", None)
    if connection is not None:
        connection.close()


def wipe_database() -> None:
    """Remove the live database file (rarely needed; refresh uses staging + swap)."""
    logger.debug(f"Wiping database at {get_database_path().as_posix()}")
    Path.unlink(get_database_path(), missing_ok=True)


def populate_with_models() -> None:
    """
    Fetch/combine models, write a staging SQLite file, then atomically replace
    ``database.db`` so readers keep serving the previous snapshot until swap.
    """
    models, provider_endpoints = get_and_clean_data()

    live_path = get_database_path()
    staging_path = get_staging_database_path()
    live_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path.unlink(missing_ok=True)

    db = initialize_database(staging_path)
    try:
        logger.debug(f"Writing {len(models)} models to staging database")
        for model in models:
            model.add_to_database(db)
        logger.debug(f"Wrote {len(models)} models to staging database")
        logger.debug(
            f"Writing {len(provider_endpoints)} provider endpoints to staging database"
        )
        for row in provider_endpoints:
            row.add_to_database(db)
        logger.debug(
            f"Wrote {len(provider_endpoints)} provider endpoints to staging database"
        )
    except Exception:
        _close_database(db)
        staging_path.unlink(missing_ok=True)
        raise

    _close_database(db)
    os.replace(staging_path, live_path)
    logger.info(
        "Replaced live database with staging snapshot (%d models, %d provider rows)",
        len(models),
        len(provider_endpoints),
    )


def get_all_models() -> list[CombinedModel]:
    path = get_database_path()
    if not path.is_file():
        logger.warning("Model database missing at %s; returning empty list", path)
        return []
    db: DataBase = initialize_database(path)
    try:
        return list(db("models"))
    finally:
        _close_database(db)


def get_all_provider_endpoints() -> list[ModelProviderEndpoint]:
    path = get_database_path()
    if not path.is_file():
        logger.warning("Model database missing at %s; returning empty list", path)
        return []
    db: DataBase = initialize_database(path)
    try:
        return list(db("model_provider_endpoints"))
    finally:
        _close_database(db)


if __name__ == "__main__":
    # Prefer: python -m llm_rankings.refresh [--force] [--source …]
    from llm_rankings.refresh import main as refresh_main

    raise SystemExit(refresh_main())
