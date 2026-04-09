from __future__ import annotations

import json
import os
from pathlib import Path


def state_dir(explicit_state_dir: str | None = None) -> Path:
    value = explicit_state_dir or os.environ.get("ROBIN_STATE_DIR")
    if not value:
        raise SystemExit(
            "Robin state directory is not configured. Pass --state-dir or set ROBIN_STATE_DIR."
        )
    return Path(value).expanduser().resolve()


def config_path(explicit_state_dir: str | None = None) -> Path:
    return state_dir(explicit_state_dir) / "robin-config.json"


def index_path(explicit_state_dir: str | None = None) -> Path:
    return state_dir(explicit_state_dir) / "robin-review-index.json"


def load_config(explicit_state_dir: str | None = None) -> dict:
    path = config_path(explicit_state_dir)
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Config not found at {path}. Create robin-config.json in the state directory first."
        ) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Config at {path} is invalid JSON: {exc}") from exc


def empty_index() -> dict:
    return {"items": {}}


def load_index(explicit_state_dir: str | None = None) -> dict:
    path = index_path(explicit_state_dir)
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


def save_index(index: dict, explicit_state_dir: str | None = None) -> None:
    path = index_path(explicit_state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, sort_keys=True)
