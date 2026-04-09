from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Entry:
    entry_id: str
    topic: str
    date_added: str
    source: str
    tags: list[str] = field(default_factory=list)
    body: str = ""

