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
    hermes_home = tmp_path / ".hermes"
    data_dir = hermes_home / "data"
    data_dir.mkdir(parents=True)

    vault_path = tmp_path / "vault"
    (vault_path / "topics").mkdir(parents=True)

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    config = {
        "vault_path": str(vault_path),
        "topics_dir": "topics",
        "min_items_before_review": 1,
        "review_cooldown_days": 60,
        "preferred_rating_scale": "1-5",
        "file_naming": "kebab",
    }
    (data_dir / "cb-config.json").write_text(json.dumps(config, indent=2))
    (data_dir / "cb-review-index.json").write_text(
        json.dumps(
            {"items": {}, "config": {"min_items_before_review": 1, "review_cooldown_days": 60}},
            indent=2,
        )
    )

    return {"tmp_path": tmp_path, "hermes_home": hermes_home, "vault_path": vault_path}
