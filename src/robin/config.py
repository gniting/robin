from __future__ import annotations

import json
import os
from pathlib import Path


def _cwd_robin_state_dir() -> Path | None:
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        state_dir = candidate / "data" / "robin"
        if (state_dir / "robin-config.json").exists():
            return state_dir
    return None


def _xdg_config_root() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


def _xdg_data_root() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))


def config_dir() -> Path:
    explicit_config = os.environ.get("ROBIN_CONFIG_FILE")
    if explicit_config:
        return Path(explicit_config).expanduser().resolve().parent
    workspace = os.environ.get("ROBIN_WORKSPACE")
    if workspace:
        return Path(workspace).expanduser().resolve() / "data" / "robin"
    discovered = _cwd_robin_state_dir()
    if discovered:
        return discovered
    robin_home = os.environ.get("ROBIN_HOME")
    if robin_home:
        return Path(robin_home) / "config"
    if os.environ.get("XDG_CONFIG_HOME"):
        return _xdg_config_root() / "robin"
    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home:
        return Path(hermes_home) / "data"
    return _xdg_config_root() / "robin"


def data_dir() -> Path:
    explicit_index = os.environ.get("ROBIN_INDEX_FILE")
    if explicit_index:
        return Path(explicit_index).expanduser().resolve().parent
    workspace = os.environ.get("ROBIN_WORKSPACE")
    if workspace:
        return Path(workspace).expanduser().resolve() / "data" / "robin"
    discovered = _cwd_robin_state_dir()
    if discovered:
        return discovered
    robin_home = os.environ.get("ROBIN_HOME")
    if robin_home:
        return Path(robin_home) / "data"
    if os.environ.get("XDG_DATA_HOME"):
        return _xdg_data_root() / "robin"
    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home:
        return Path(hermes_home) / "data"
    return _xdg_data_root() / "robin"


def config_path() -> Path:
    explicit_config = os.environ.get("ROBIN_CONFIG_FILE")
    if explicit_config:
        return Path(explicit_config).expanduser().resolve()
    return config_dir() / "robin-config.json"


def index_path() -> Path:
    explicit_index = os.environ.get("ROBIN_INDEX_FILE")
    if explicit_index:
        return Path(explicit_index).expanduser().resolve()
    return data_dir() / "robin-review-index.json"


def load_config() -> dict:
    path = config_path()
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise SystemExit(f"Config not found at {path}. Run install.sh first.") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Config at {path} is invalid JSON: {exc}") from exc


def empty_index() -> dict:
    return {"items": {}}


def load_index() -> dict:
    path = index_path()
    if path.exists():
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Review index at {path} is invalid JSON: {exc}") from exc
    else:
        data = empty_index()

    data.setdefault("items", {})
    return data


def save_index(index: dict) -> None:
    path = index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, sort_keys=True)
