from __future__ import annotations

import os
from pathlib import Path

_ENV_STATE: tuple[Path, int, int] | None = None
_ENV_LOADED_KEYS: set[str] = set()


def _parse_env_file(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


def load_environment(env_path: Path | str = ".env") -> None:
    global _ENV_STATE

    path = Path(env_path).resolve()
    if not path.exists():
        missing_state = (path, -1, -1)
        if _ENV_STATE == missing_state:
            return
        _ENV_STATE = missing_state
        return

    stat = path.stat()
    state = (path, stat.st_mtime_ns, stat.st_size)
    if _ENV_STATE == state:
        return

    for key, value in _parse_env_file(path).items():
        if key in _ENV_LOADED_KEYS or key not in os.environ:
            os.environ[key] = value
            _ENV_LOADED_KEYS.add(key)

    _ENV_STATE = state


def get_bool_env(name: str, default: bool = False) -> bool:
    load_environment()
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_int_env(name: str, default: int) -> int:
    load_environment()
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default
