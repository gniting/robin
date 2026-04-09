from __future__ import annotations

import json
from datetime import datetime, timezone

from robin.config import load_index, save_index
from robin.parser import SEPARATOR, load_all_entries
from robin.review_logic import parse_timestamp, pick_best_candidate, rate_item


def test_review_uses_entry_ids_for_same_day_duplicates(robin_env):
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
                SEPARATOR.strip(),
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

    now = datetime.now(timezone.utc).isoformat()
    index = {
        "items": {
            "20260408-a1f3": {
                "id": "20260408-a1f3",
                "topic": "ai-reasoning",
                "date": "2026-04-08",
                "rating": None,
                "last_surfaced": now,
                "times_surfaced": 1,
            },
            "20260408-b7k2": {
                "id": "20260408-b7k2",
                "topic": "ai-reasoning",
                "date": "2026-04-08",
                "rating": None,
                "last_surfaced": None,
                "times_surfaced": 0,
            },
        },
        "config": {"min_items_before_review": 1, "review_cooldown_days": 60},
    }
    save_index(index)

    candidate = pick_best_candidate(load_index(), load_all_entries(json.loads((robin_env["hermes_home"] / "data" / "cb-config.json").read_text())), {"review_cooldown_days": 60})
    assert candidate is not None
    _, entry = candidate
    assert entry.entry_id == "20260408-b7k2"
    assert entry.body == "Second entry."


def test_rate_item_writes_parseable_timestamp(robin_env):
    index = load_index()
    index["items"]["20260408-a1f3"] = {
        "id": "20260408-a1f3",
        "topic": "ai-reasoning",
        "date": "2026-04-08",
        "rating": None,
        "last_surfaced": None,
        "times_surfaced": 0,
    }

    item = rate_item(index, "20260408-a1f3", 5)
    parsed = parse_timestamp(item["last_surfaced"])

    assert parsed.tzinfo is not None
    assert item["times_surfaced"] == 1
    assert item["rating"] == 5

