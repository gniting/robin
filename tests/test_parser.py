from __future__ import annotations

from robin.parser import parse_entry
from robin.serializer import build_entry, serialize_entry


def test_serialize_and_parse_round_trip():
    entry = build_entry(
        topic="AI Reasoning",
        content="Clear thinking beats ornament.",
        source="https://example.com",
        note="Keep this near writing advice.",
        tags=["writing", "clarity"],
        date_added="2026-04-08",
        entry_id="20260408-a1f3",
    )

    parsed = parse_entry(serialize_entry(entry), "ai-reasoning")

    assert parsed.entry_id == "20260408-a1f3"
    assert parsed.topic == "ai-reasoning"
    assert parsed.source == "https://example.com"
    assert parsed.tags == ["writing", "clarity"]
    assert "Robin note" in parsed.body


def test_parse_entry_generates_legacy_fallback_id():
    parsed = parse_entry(
        "date_added: 2026-04-08\nsource: \ntags: [notes]\n\nSomething worth keeping.",
        "notes",
    )

    assert parsed.entry_id.startswith("legacy-")
    assert parsed.date_added == "2026-04-08"

