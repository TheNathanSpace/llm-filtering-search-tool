import datetime
import logging
import os
import shutil
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


def setup_logging(level: str = "DEBUG"):
    """
    Sets up basic logging configuration.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s.%(msecs)03d | %(funcName)-25s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


ENV_VARS_LOGGED = False


def validate_env_vars() -> Path:
    """
    Validates the presence of an .env file and loads environment variables.

    :return: The Path to the .env file.
    """
    global ENV_VARS_LOGGED
    if not ENV_VARS_LOGGED:
        logging.debug("Validating environment variables")
        ENV_VARS_LOGGED = True
    dotenv_path = find_dotenv()
    if not dotenv_path:
        raise ValueError("No .env file found")
    load_dotenv(dotenv_path)
    return Path(dotenv_path)


DATA_DIR_LOGGED = False


def get_data_dir():
    """
    Gets or creates the data directory specified in the environment variables.

    :return: The Path to the data directory.
    """
    global DATA_DIR_LOGGED
    if not DATA_DIR_LOGGED:
        logging.debug("Getting data directory")
    env_file = validate_env_vars()
    data_dir = env_file.parent / get_env_var("DATA_DIR")
    data_dir.mkdir(parents=True, exist_ok=True)
    if not DATA_DIR_LOGGED:
        DATA_DIR_LOGGED = True
        logging.debug(f"Data directory is: {data_dir.as_posix()}")
    return data_dir


INTERMEDIATE_DIR_LOGGED = False


def get_intermediate_data_dir():
    """
    Gets or creates the intermediate data directory (data/intermediate/).

    :return: The Path to the intermediate data directory.
    """
    global INTERMEDIATE_DIR_LOGGED
    if not INTERMEDIATE_DIR_LOGGED:
        logging.debug("Getting intermediate data directory")
    data_dir = get_data_dir()
    intermediate_dir = data_dir / "intermediate"
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    if not INTERMEDIATE_DIR_LOGGED:
        INTERMEDIATE_DIR_LOGGED = True
        logging.debug(f"Intermediate data directory is: {intermediate_dir.as_posix()}")
    return intermediate_dir


def get_provider_dir() -> Path:
    intermediate_dir = get_intermediate_data_dir()
    provider_dir = intermediate_dir / "providers"
    provider_dir.mkdir(parents=True, exist_ok=True)
    return provider_dir


def erase_data_dir():
    logging.debug("Erasing data directory")
    data_dir = get_data_dir()
    if data_dir.exists():
        shutil.rmtree(data_dir)
        logging.debug(f"Data directory erased: {data_dir.as_posix()}")
    else:
        logging.debug(f"Data directory does not exist: {data_dir.as_posix()}")


LOGGED_ENV_VARS = set()


def get_env_var(name: str) -> str:
    """
    Retrieves the value of an environment variable.

    :param name: The name of the environment variable.
    :return: The value of the environment variable.
    """
    global LOGGED_ENV_VARS
    if name not in LOGGED_ENV_VARS:
        logging.debug(f"Getting environment variable: {name}")
        LOGGED_ENV_VARS.add(name)
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


def invert_dict(d: dict) -> dict:
    return {v: k for k, v in d.items()}


def string_is_only_in_one(s: str, string_1: str, string_2: str) -> bool:
    only_in_first = s in string_1 and s not in string_2
    only_in_second = s in string_2 and s not in string_1
    return only_in_first or only_in_second


def sort_dict(d: dict, by_value: bool = False) -> dict:
    return dict(sorted(d.items(), key=lambda item: item[1] if by_value else item[0]))


def split_to_words(phrase: str) -> list[str]:
    return [w for w in phrase.split(" ") if w]


def safe_rename_dict_key(d: dict, old_key: str, new_key: str):
    """Updates dict in-place."""
    if old_key in d:
        d[new_key] = d.pop(old_key)


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Merges two dictionaries. Recursively merges child dictionaries.
    Throws a ValueError if there are overlapping non-dictionary keys.

    :param dict1: The first dictionary.
    :param dict2: The second dictionary.
    :return: The merged dictionary.
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                raise ValueError(f"Overlapping non-dictionary keys found: {key}")
        else:
            result[key] = value
    return result


def safe_delete_key(d: dict, key: str):
    if key in d:
        del d[key]


def safe_add_null_key(d: dict, key: str):
    if key not in d:
        d[key] = None
