import datetime
import logging
import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


def setup_logging():
    """
    Sets up basic logging configuration.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d | %(funcName)-25s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def validate_env_vars() -> Path:
    """
    Validates the presence of an .env file and loads environment variables.

    :return: The Path to the .env file.
    """
    logging.debug("Validating environment variables")
    dotenv_path = find_dotenv()
    if not dotenv_path:
        raise ValueError("No .env file found")
    load_dotenv(dotenv_path)
    return Path(dotenv_path)


def get_data_dir():
    """
    Gets or creates the data directory specified in the environment variables.

    :return: The Path to the data directory.
    """
    logging.debug("Getting data directory")
    env_file = validate_env_vars()
    data_dir = env_file.parent / get_env_var("DATA_DIR")
    data_dir.mkdir(parents=True, exist_ok=True)
    logging.debug(f"Data directory is: {data_dir.as_posix()}")
    return data_dir


def get_env_var(name: str) -> str:
    """
    Retrieves the value of an environment variable.

    :param name: The name of the environment variable.
    :return: The value of the environment variable.
    """
    logging.debug(f"Getting environment variable: {name}")
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Environment variable is not set: {name}")
    return value


def unix_epoch_to_utc(timestamp: int) -> str:
    """
    Converts a Unix epoch timestamp to UTC ISO 8601 format.

    :param timestamp: The Unix epoch timestamp.
    :return: The timestamp in UTC ISO 8601 format.
    """
    return datetime.datetime.fromtimestamp(timestamp, datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_to_unix_epoch(utc_datetime: datetime.datetime | str) -> int:
    """
    Converts a datetime object in UTC to a Unix epoch timestamp. Will forcibly set the timezone to UTC, so ensure
    that the datetime object actually IS in UTC, or else the result will be unexpected.

    :param utc_datetime: The datetime object in UTC.
    :return: The Unix epoch timestamp.
    """
    if isinstance(utc_datetime, str):
        utc_datetime = datetime.datetime.fromisoformat(utc_datetime)
    # The .replace() forces the given datetime to be in UTC
    return int(utc_datetime.replace(tzinfo=datetime.UTC).timestamp())
