from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_selftest_script_passes():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "selftest.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "14/14 passed" in proc.stdout


def test_selftest_state_dir_respects_custom_config_dirs(tmp_path):
    state_dir = tmp_path / "data" / "robin"
    (state_dir / "custom-topics").mkdir(parents=True)
    (state_dir / "custom-media").mkdir()
    (state_dir / "robin-config.json").write_text(
        json.dumps({"topics_dir": "custom-topics", "media_dir": "custom-media"}),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "selftest.py"), "--state-dir", str(state_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "3/3 passed" in proc.stdout
