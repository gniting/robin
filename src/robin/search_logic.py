from __future__ import annotations

from robin.models import Entry


def search_entries(entries: list[Entry], query: str) -> list[Entry]:
    query_lower = query.lower()
    return [
        entry
        for entry in entries
        if query_lower in entry.body.lower() or query_lower in entry.source.lower()
    ]


def filter_by_topic(entries: list[Entry], topic: str) -> list[Entry]:
    return [entry for entry in entries if entry.topic == topic]


def filter_by_tags(entries: list[Entry], tags: list[str]) -> list[Entry]:
    normalized = {tag.lower() for tag in tags if tag.strip()}
    return [
        entry
        for entry in entries
        if normalized.issubset({tag.lower() for tag in entry.tags})
    ]

