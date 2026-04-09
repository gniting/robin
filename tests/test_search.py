from __future__ import annotations

import json

from robin.config import load_index, save_index
from scripts import search, topics


def test_search_and_topics_json(robin_env, monkeypatch, capsys):
    topic_file = robin_env["vault_path"] / "topics" / "writing.md"
    topic_file.write_text(
        "\n".join(
            [
                "id: 20260408-a1f3",
                "date_added: 2026-04-08",
                "source: https://example.com",
                "tags: [writing, clarity]",
                "",
                "Write as if you were speaking to a smart friend.",
                "",
            ]
        )
    )

    index = load_index()
    index["items"]["20260408-a1f3"] = {
        "id": "20260408-a1f3",
        "topic": "writing",
        "date": "2026-04-08",
        "rating": 4,
        "last_surfaced": None,
        "times_surfaced": 0,
    }
    save_index(index)

    monkeypatch.setattr("sys.argv", ["search.py", "smart friend", "--json"])
    search.main()
    search_output = json.loads(capsys.readouterr().out)
    assert search_output["count"] == 1
    assert search_output["entries"][0]["rating"] == 4

    monkeypatch.setattr("sys.argv", ["topics.py", "--json"])
    topics.main()
    topics_output = json.loads(capsys.readouterr().out)
    assert topics_output == [
        {
            "topic": "writing",
            "filename": "writing.md",
            "entries": 1,
            "rated": 1,
            "unrated": 0,
        }
    ]
