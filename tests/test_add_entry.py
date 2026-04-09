from __future__ import annotations

import json

from robin.config import load_index
from scripts import add_entry


def test_add_entry_writes_markdown_and_index(robin_env, monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "add_entry.py",
            "--topic",
            "AI Reasoning",
            "--content",
            "Write clearly.",
            "--source",
            "https://example.com",
            "--tags",
            "writing,clarity",
            "--json",
        ],
    )

    add_entry.main()
    output = json.loads(capsys.readouterr().out)

    topic_file = robin_env["vault_path"] / "topics" / "ai-reasoning.md"
    content = topic_file.read_text()
    assert f"id: {output['id']}" in content
    assert "Write clearly." in content

    index = load_index()
    assert output["id"] in index["items"]
    assert index["items"][output["id"]]["topic"] == "ai-reasoning"

