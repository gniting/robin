from __future__ import annotations

import pytest

from robin.config import config_dir, config_path, data_dir, index_path, load_config, load_index


def test_load_config_missing_file_exits_cleanly(robin_env):
    config_path().unlink()

    with pytest.raises(SystemExit, match="Config not found"):
        load_config()


def test_load_config_invalid_json_exits_cleanly(robin_env):
    config_path().write_text("{invalid json", encoding="utf-8")

    with pytest.raises(SystemExit, match="invalid JSON"):
        load_config()


def test_load_index_invalid_json_exits_cleanly(robin_env):
    index_path().write_text("{invalid json", encoding="utf-8")

    with pytest.raises(SystemExit, match="invalid JSON"):
        load_index()


def test_paths_respect_robin_home(robin_env):
    assert config_dir() == robin_env["config_dir"]
    assert data_dir() == robin_env["data_dir"]
    assert config_path() == robin_env["config_dir"] / "robin-config.json"
    assert index_path() == robin_env["data_dir"] / "robin-review-index.json"


def test_paths_fall_back_to_xdg(monkeypatch, tmp_path):
    monkeypatch.delenv("ROBIN_HOME", raising=False)
    monkeypatch.delenv("HERMES_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

    assert config_dir() == tmp_path / "cfg" / "robin"
    assert data_dir() == tmp_path / "data" / "robin"


def test_paths_fall_back_to_hermes_home_for_compat(monkeypatch, tmp_path):
    monkeypatch.delenv("ROBIN_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

    assert config_dir() == tmp_path / ".hermes" / "data"
    assert data_dir() == tmp_path / ".hermes" / "data"


def test_data_dir_prefers_hermes_home_when_only_xdg_config_is_set(monkeypatch, tmp_path):
    monkeypatch.delenv("ROBIN_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

    assert config_dir() == tmp_path / "cfg" / "robin"
    assert data_dir() == tmp_path / ".hermes" / "data"
