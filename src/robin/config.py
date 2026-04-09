from __future__ import annotations

import json
import os
from pathlib import Path


def hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))


def data_dir() -> Path:
    return hermes_home() / "data"


def config_path() -> Path:
    return data_dir() / "cb-config.json"


def index_path() -> Path:
    return data_dir() / "cb-review-index.json"


def load_config() -> dict:
    with config_path().open() as f:
        return json.load(f)


def empty_index(config: dict | None = None) -> dict:
    review_config = {
        "min_items_before_review": (config or {}).get("min_items_before_review", 30),
        "review_cooldown_days": (config or {}).get("review_cooldown_days", 60),
    }
    return {"items": {}, "config": review_config}


def load_index(config: dict | None = None) -> dict:
    path = index_path()
    if path.exists():
        with path.open() as f:
            data = json.load(f)
    else:
        data = empty_index(config)

    data.setdefault("items", {})
    data.setdefault("config", empty_index(config)["config"])
    return data


def save_index(index: dict) -> None:
    path = index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(index, f, indent=2, sort_keys=True)

