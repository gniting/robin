from __future__ import annotations

from datetime import date
from uuid import uuid4

from robin.models import Entry
from robin.parser import topic_slug


def generate_entry_id(date_added: str | None = None) -> str:
    stamp = (date_added or str(date.today())).replace("-", "")
    return f"{stamp}-{uuid4().hex[:4]}"


def build_entry(
    topic: str,
    content: str,
    source: str | None,
    note: str | None,
    tags: list[str],
    date_added: str,
    entry_id: str | None = None,
) -> Entry:
    body_parts: list[str] = []
    if source:
        body_parts.append(f"**Source:** {source}")
        body_parts.append("")
    body_parts.append(content.strip())
    if note:
        body_parts.append("")
        body_parts.append(f"**Robin note:** {note.strip()}")

    return Entry(
        entry_id=entry_id or generate_entry_id(date_added),
        topic=topic_slug(topic),
        date_added=date_added,
        source=(source or "").strip(),
        tags=tags,
        body="\n".join(body_parts).strip(),
    )


def serialize_entry(entry: Entry) -> str:
    lines = [
        f"id: {entry.entry_id}",
        f"date_added: {entry.date_added}",
        f"source: {entry.source}",
        f"tags: [{', '.join(entry.tags)}]",
        "",
        entry.body.strip(),
    ]
    return "\n".join(lines).rstrip()

