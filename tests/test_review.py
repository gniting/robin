from __future__ import annotations

import json
from datetime import datetime, timezone

from robin.config import load_index, save_index
from robin.parser import SEPARATOR, load_all_entries
from robin.review_logic import parse_timestamp, pick_best_candidate, rate_item
from robin.serializer import build_media_entry, build_text_entry, serialize_entry
from scripts import review


def test_review_uses_entry_ids_for_same_day_duplicates(robin_env):
    topic_file = robin_env["vault_path"] / "topics" / "ai-reasoning.md"
    topic_file.write_text(
        f"{SEPARATOR}".join(
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
    }
    save_index(index)

    candidate = pick_best_candidate(
        load_index(),
        load_all_entries(json.loads((robin_env["config_dir"] / "robin-config.json").read_text(encoding="utf-8"))),
        {"review_cooldown_days": 60},
    )
    assert candidate is not None
    _, entry = candidate
    assert entry.entry_id == "20260408-b7k2"
    assert entry.description == "Second description."
    assert entry.body == "Second entry."


def test_review_surfaces_media_metadata(robin_env):
    topic_file = robin_env["vault_path"] / "topics" / "poetry.md"
    topic_file.write_text(
        serialize_entry(
            build_media_entry(
                topic="Poetry",
                media_kind="image",
                media_source="media/poetry/20260408-a1f3.png",
                description="A photographed excerpt to revisit.",
                creator="Mary Oliver",
                published_at="1986",
                summary="An excerpt about attention and observation.",
                content="Opening lines from the page.",
                source="",
                note="",
                tags=["poetry"],
                date_added="2026-04-08",
                entry_id="20260408-a1f3",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    index = {
        "items": {
            "20260408-a1f3": {
                "id": "20260408-a1f3",
                "topic": "poetry",
                "date": "2026-04-08",
                "rating": None,
                "last_surfaced": None,
                "times_surfaced": 0,
            }
        },
    }
    save_index(index)

    candidate = pick_best_candidate(
        load_index(),
        load_all_entries(json.loads((robin_env["config_dir"] / "robin-config.json").read_text(encoding="utf-8"))),
        {"review_cooldown_days": 60},
    )
    assert candidate is not None
    _, entry = candidate
    assert entry.entry_type == "image"
    assert entry.media_source == "media/poetry/20260408-a1f3.png"
    assert entry.creator == "Mary Oliver"
    assert entry.summary.startswith("An excerpt")


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


def test_review_rejects_non_numeric_rating(robin_env, monkeypatch, capsys):
    index = load_index()
    index["items"]["20260408-a1f3"] = {
        "id": "20260408-a1f3",
        "topic": "ai-reasoning",
        "date": "2026-04-08",
        "rating": None,
        "last_surfaced": None,
        "times_surfaced": 0,
    }
    save_index(index)

    monkeypatch.setattr("sys.argv", ["review.py", "--rate", "20260408-a1f3", "abc"])

    try:
        review.main()
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("Expected SystemExit for invalid rating")

    assert "Rating must be a number between 1 and 5." in capsys.readouterr().out
