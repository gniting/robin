from __future__ import annotations

from robin.index import rebuild_index
from robin.parser import load_all_entries


def test_reindex_preserves_legacy_review_state(robin_env):
    topic_file = robin_env["vault_path"] / "topics" / "ai-reasoning.md"
    topic_file.write_text(
        "\n".join(
            [
                "id: 20260408-a1f3",
                "date_added: 2026-04-08",
                "source: ",
                "tags: [writing]",
                "",
                "First entry.",
                "***",
                "id: 20260408-b7k2",
                "date_added: 2026-04-08",
                "source: ",
                "tags: [writing]",
                "",
                "Second entry.",
                "",
            ]
        )
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
        "config": {"min_items_before_review": 1, "review_cooldown_days": 60},
    }

    rebuilt = rebuild_index(load_all_entries({
        "vault_path": str(robin_env["vault_path"]),
        "topics_dir": "topics",
    }), old_index)

    assert rebuilt["items"]["20260408-a1f3"]["rating"] == 2
    assert rebuilt["items"]["20260408-a1f3"]["times_surfaced"] == 4
    assert rebuilt["items"]["20260408-b7k2"]["rating"] == 5

