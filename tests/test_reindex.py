from __future__ import annotations

from robin.index import rebuild_index
from robin.parser import load_all_entries
from robin.serializer import build_text_entry, serialize_entry


def test_reindex_preserves_legacy_review_state(robin_env):
    topic_file = robin_env["vault_path"] / "topics" / "ai-reasoning.md"
    topic_file.write_text(
        "\n***\n".join(
            [
                serialize_entry(
                    build_text_entry(
                        topic="AI Reasoning",
                        content="First entry.",
                        description="First description.",
                        source="",
                        note="",
                        tags=["writing"],
                        date_added="2026-04-08",
                        entry_id="20260408-a1f3",
                    )
                ),
                serialize_entry(
                    build_text_entry(
                        topic="AI Reasoning",
                        content="Second entry.",
                        description="Second description.",
                        source="",
                        note="",
                        tags=["writing"],
                        date_added="2026-04-08",
                        entry_id="20260408-b7k2",
                    )
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    old_index = {
        "items": {
            "ai-reasoning:2026-04-08:001": {
                "rating": 2,
                "last_surfaced": "2026-04-01T10:00:00+00:00",
                "times_surfaced": 4,
            },
            "ai-reasoning:2026-04-08:002": {
                "rating": 5,
                "last_surfaced": None,
                "times_surfaced": 1,
            },
        },
    }

    rebuilt = rebuild_index(load_all_entries({
        "vault_path": str(robin_env["vault_path"]),
        "topics_dir": "topics",
    }), old_index)

    assert rebuilt["items"]["20260408-a1f3"]["rating"] == 2
    assert rebuilt["items"]["20260408-a1f3"]["times_surfaced"] == 4
    assert rebuilt["items"]["20260408-b7k2"]["rating"] == 5
