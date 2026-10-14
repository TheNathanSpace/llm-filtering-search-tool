import datetime
import logging
import os
import shutil
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger(__name__)

_ENV_FILE: Path | None = None
_ENV_READY = False
_LOGGING_CONFIGURED = False
_LOG_FORMAT = "%(asctime)s.%(msecs)03d | %(name)-35s | %(funcName)-25s | %(levelname)-8s | %(message)s"
_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _resolve_log_level(level_name: str) -> int:
    level = logging.getLevelNamesMapping().get(level_name.upper())
    if level is None:
        raise ValueError(f"Invalid LOG_LEVEL: {level_name}")
    return level


def _prune_log_files(logs_dir: Path, keep: int, current: Path) -> None:
    """Delete oldest ``*.log`` files until at most ``keep`` remain (never delete ``current``).

    Symlinks (including ``latest.log``) are ignored.
    """
    current_resolved = current.resolve()
    others = sorted(
        (p for p in logs_dir.glob("*.log") if p.is_file() and not p.is_symlink() and p.resolve() != current_resolved),
        key=lambda p: p.name,
    )
    retain_others = max(keep - 1, 0)
    to_delete = others if retain_others == 0 else others[:-retain_others]
    for path in to_delete:
        path.unlink(missing_ok=True)
        logger.debug(f"Deleted old log file: {path.as_posix()}")


def _update_latest_log_symlink(logs_dir: Path, log_path: Path) -> Path:
    """Point ``logs_dir/latest.log`` at ``log_path`` (relative symlink)."""
    latest = logs_dir / "latest.log"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    latest.symlink_to(log_path.name)
    return latest


def _discover_env_file() -> Path | None:
    """
    Locate a ``.env`` without an explicit path.

    ``find_dotenv()`` walks from the caller module path. That works for an editable
    checkout, but fails in the prod image where the package lives under
    site-packages — so also try cwd and the Compose mount at ``/app/.env``.
    """
    for candidate in (
        find_dotenv(),
        find_dotenv(usecwd=True),
        Path.cwd() / ".env",
        Path("/app/.env"),
    ):
        if not candidate:
            continue
        path = Path(candidate).expanduser().resolve()
        if path.is_file():
            return path
    return None


def configure_env_file(path: str | Path | None = None) -> Path | None:
    """
    Load a ``.env`` file when one is available.

    Variables already set in the process environment are kept, so a Compose
    ``environment:`` block wins over a file. When no file is requested and none
    is found, the process environment is used as-is.

    :param path: Explicit path to a ``.env`` file. When ``None``, uses
        ``LLM_RANKINGS_ENV_FILE`` if set, otherwise discovery (see
        ``_discover_env_file``). An explicit path that is missing raises.
    :return: Resolved path to the loaded file, or ``None`` when configuration
        comes only from the process environment.
    """
    global _ENV_FILE, _ENV_READY

    if path is not None:
        env_file: Path | None = Path(path).expanduser().resolve()
    else:
        from_env = os.environ.get("LLM_RANKINGS_ENV_FILE")
        if from_env:
            env_file = Path(from_env).expanduser().resolve()
        else:
            env_file = _discover_env_file()

    if env_file is None:
        _ENV_FILE = None
        _ENV_READY = True
        return None

    if not env_file.is_file():
        raise ValueError(f".env file not found: {env_file.as_posix()}")

    load_dotenv(env_file, override=False)
    _ENV_FILE = env_file
    _ENV_READY = True
    return env_file


def get_env_file() -> Path | None:
    """Return the configured ``.env`` path, or ``None`` when only the process environment is used."""
    if not _ENV_READY:
        configure_env_file()
    return _ENV_FILE


def data_dir_from_env() -> Path:
    """
    Resolve ``DATA_DIR``.

    Absolute paths are used as-is. Relative paths are resolved against the
    ``.env`` file's directory when one was loaded, otherwise against the
    process working directory.
    """
    get_env_file()
    raw = os.environ.get("DATA_DIR")
    if not raw:
        raise ValueError("Environment variable is not set: DATA_DIR")
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    anchor = _ENV_FILE.parent if _ENV_FILE is not None else Path.cwd()
    return anchor / path


def bootstrap_env_from_argv() -> Path | None:
    """
    Load ``.env`` before other back-end setup.

    Honors ``--env-file`` / ``-e`` on ``sys.argv`` (removed after parsing), then
    ``LLM_RANKINGS_ENV_FILE``, then env-file discovery.
    """
    if _ENV_READY:
        return _ENV_FILE

    argv = sys.argv
    for index, arg in enumerate(argv):
        if arg in ("--env-file", "-e") and index + 1 < len(argv):
            env_path = argv[index + 1]
            del argv[index : index + 2]
            return configure_env_file(env_path)

    return configure_env_file()


def setup_logging() -> Path:
    """
    Configure the root logger from the environment (inherited by named module loggers).

    Writes to stdout and ``DATA_DIR/logs/{YYYY-MM-DD}-{HHMMSS}.log``, and updates
    ``DATA_DIR/logs/latest.log`` as a symlink to that file. After creating the new file,
    deletes the oldest logs so at most ``LOG_FILE_COUNT`` files remain.

    :return: Path to the new log file.
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        raise RuntimeError("setup_logging() has already been called")

    get_env_file()

    level_name = os.environ.get("LOG_LEVEL")
    if not level_name:
        raise ValueError("Environment variable is not set: LOG_LEVEL")
    level = _resolve_log_level(level_name)

    keep_raw = os.environ.get("LOG_FILE_COUNT")
    if not keep_raw:
        raise ValueError("Environment variable is not set: LOG_FILE_COUNT")
    try:
        keep = int(keep_raw)
    except ValueError as e:
        raise ValueError(f"LOG_FILE_COUNT must be an integer: {keep_raw}") from e
    if keep < 1:
        raise ValueError(f"LOG_FILE_COUNT must be >= 1: {keep}")

    logs_dir = data_dir_from_env() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_path = logs_dir / f"{stamp}.log"
    if log_path.exists():
        log_path = logs_dir / f"{stamp}-{datetime.datetime.now().strftime('%f')}.log"

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_LOG_DATEFMT)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=level, handlers=[stdout_handler, file_handler], force=True)
    latest = _update_latest_log_symlink(logs_dir, log_path)
    _prune_log_files(logs_dir, keep, log_path)
    _LOGGING_CONFIGURED = True

    logger.info(
        f"Logging configured: level={level_name.upper()}, file={log_path.as_posix()}, "
        f"latest={latest.as_posix()}, keeping up to {keep} log file(s)"
    )
    return log_path


ENV_VARS_LOGGED = False


def validate_env_vars() -> Path | None:
    """
    Load ``.env`` when one exists. The process environment is enough when it does not.

    :return: The path to the ``.env`` file, or ``None``.
    """
    global ENV_VARS_LOGGED
    if not ENV_VARS_LOGGED:
        logger.debug("Validating environment variables")
        ENV_VARS_LOGGED = True
    return get_env_file()


DATA_DIR_LOGGED = False


def get_data_dir():
    """
    Gets or creates the data directory specified in the environment variables.

    :return: The Path to the data directory.
    """
    global DATA_DIR_LOGGED
    if not DATA_DIR_LOGGED:
        logger.debug("Getting data directory")
    validate_env_vars()
    data_dir = data_dir_from_env()
    data_dir.mkdir(parents=True, exist_ok=True)
    if not DATA_DIR_LOGGED:
        DATA_DIR_LOGGED = True
        logger.debug(f"Data directory is: {data_dir.as_posix()}")
    return data_dir


INTERMEDIATE_DIR_LOGGED = False


def get_intermediate_data_dir():
    """
    Gets or creates the intermediate data directory (data/intermediate/).

    :return: The Path to the intermediate data directory.
    """
    global INTERMEDIATE_DIR_LOGGED
    if not INTERMEDIATE_DIR_LOGGED:
        logger.debug("Getting intermediate data directory")
    data_dir = get_data_dir()
    intermediate_dir = data_dir / "intermediate"
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    if not INTERMEDIATE_DIR_LOGGED:
        INTERMEDIATE_DIR_LOGGED = True
        logger.debug(f"Intermediate data directory is: {intermediate_dir.as_posix()}")
    return intermediate_dir


RAW_DIR_LOGGED = False


def get_raw_data_dir() -> Path:
    global RAW_DIR_LOGGED
    if not RAW_DIR_LOGGED:
        logger.debug("Getting RAW data directory")
    raw_dir = get_intermediate_data_dir() / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not RAW_DIR_LOGGED:
        RAW_DIR_LOGGED = True
        logger.debug(f"Raw data directory is: {raw_dir.as_posix()}")
    return raw_dir


CACHE_DIR_LOGGED = False

# Shared ceiling for OpenRouter / models.dev disk caches and the refresh gate.
REFRESH_MAX_AGE_SECONDS = 24 * 60 * 60


def cache_file_is_fresh(path: Path, max_age_seconds: float = REFRESH_MAX_AGE_SECONDS) -> bool:
    """Return True if ``path`` exists and its mtime is younger than ``max_age_seconds``."""
    if not path.is_file():
        return False
    age = datetime.datetime.now().timestamp() - path.stat().st_mtime
    return age < max_age_seconds


def get_cache_dir() -> Path:
    """
    Durable HTTP/response cache under ``DATA_DIR/cache/``.

    Survives ``erase_data_dir()`` so OpenRouter, models.dev, Hugging Face, and opt-in
    web enrichment caches/ledgers are not re-hit on every local wipe.
    """
    global CACHE_DIR_LOGGED
    if not CACHE_DIR_LOGGED:
        logger.debug("Getting cache directory")
    cache_dir = get_data_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not CACHE_DIR_LOGGED:
        CACHE_DIR_LOGGED = True
        logger.debug(f"Cache directory is: {cache_dir.as_posix()}")
    return cache_dir


def erase_data_dir():
    """Erase ``DATA_DIR`` contents except the durable ``cache/`` directory."""
    logger.debug("Erasing data directory (preserving cache/)")
    data_dir = get_data_dir()
    if not data_dir.exists():
        logger.debug(f"Data directory does not exist: {data_dir.as_posix()}")
        return

    cache_dir = data_dir / "cache"
    preserved: Path | None = None
    if cache_dir.exists():
        preserved = data_dir.parent / f".{data_dir.name}-cache-preserve"
        if preserved.exists():
            shutil.rmtree(preserved)
        shutil.move(str(cache_dir), str(preserved))

    shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    if preserved is not None and preserved.exists():
        shutil.move(str(preserved), str(data_dir / "cache"))

    logger.debug(f"Data directory erased (cache preserved): {data_dir.as_posix()}")


LOGGED_ENV_VARS = set()


def get_env_var(name: str) -> str:
    """
    Retrieves the value of an environment variable.

    :param name: The name of the environment variable.
    :return: The value of the environment variable.
    """
    global LOGGED_ENV_VARS
    if name not in LOGGED_ENV_VARS:
        logger.debug(f"Getting environment variable: {name}")
        LOGGED_ENV_VARS.add(name)
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Environment variable is not set: {name}")
    return value


def is_truthy_env(name: str) -> bool:
    """True when ``name`` is set to a common truthy string (1/true/yes/on)."""
    raw = (os.environ.get(name) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")
