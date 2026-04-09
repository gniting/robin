from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture()
def robin_env(tmp_path, monkeypatch):
    robin_home = tmp_path / ".robin"
    config_dir = robin_home / "config"
    data_dir = robin_home / "data"
    config_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)

    vault_path = tmp_path / "vault"
    (vault_path / "topics").mkdir(parents=True)

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HERMES_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("ROBIN_HOME", str(robin_home))

    config = {
        "vault_path": str(vault_path),
        "topics_dir": "topics",
        "media_dir": "media",
        "min_items_before_review": 1,
        "review_cooldown_days": 60,
        "preferred_rating_scale": "1-5",
        "file_naming": "kebab",
    }
    (config_dir / "robin-config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (data_dir / "robin-review-index.json").write_text(
        json.dumps({"items": {}}, indent=2),
        encoding="utf-8",
    )

    return {
        "tmp_path": tmp_path,
        "robin_home": robin_home,
        "config_dir": config_dir,
        "data_dir": data_dir,
        "vault_path": vault_path,
    }
