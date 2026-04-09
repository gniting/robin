from __future__ import annotations

import hashlib
from pathlib import Path

from robin.models import Entry

SEPARATOR = "\n***\n"


def topic_to_filename(topic: str) -> str:
    return topic.strip().lower().replace(" ", "-") + ".md"


def topic_slug(topic: str) -> str:
    return topic_to_filename(topic).removesuffix(".md")


def topics_dir(config: dict) -> Path:
    return Path(config["vault_path"]) / config.get("topics_dir", "topics")


def parse_tags(raw_value: str) -> list[str]:
    value = raw_value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    if not value:
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def parse_frontmatter_and_body(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    frontmatter: dict[str, str | list[str]] = {}
    body_start = None

    for i, line in enumerate(lines):
        if not line.strip():
            body_start = i + 1
            break
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        normalized_key = key.strip().lower()
        normalized_value = value.strip()
        if normalized_key == "tags":
            frontmatter["tags"] = parse_tags(normalized_value)
        else:
            frontmatter[normalized_key] = normalized_value

    if body_start is None:
        raise ValueError("Entry frontmatter must be followed by a blank line.")

    body = "\n".join(lines[body_start:]).strip()
    return frontmatter, body


def parse_entry(text: str, topic: str) -> Entry:
    frontmatter, body = parse_frontmatter_and_body(text.strip())
    entry_id = str(frontmatter.get("id", "")).strip()
    date_added = str(frontmatter.get("date_added", "")).strip()
    if not date_added:
        raise ValueError("Entry is missing required date_added field.")
    source = str(frontmatter.get("source", "")).strip()
    tags = list(frontmatter.get("tags", []))
    if not entry_id:
        fingerprint = hashlib.sha1(
            f"{topic}\n{date_added}\n{source}\n{','.join(tags)}\n{body}".encode("utf-8")
        ).hexdigest()[:10]
        entry_id = f"legacy-{fingerprint}"

    return Entry(
        entry_id=entry_id,
        topic=topic,
        date_added=date_added,
        source=source,
        tags=tags,
        body=body,
    )


def load_topic_entries(filepath: Path) -> list[Entry]:
    content = filepath.read_text().strip()
    if not content:
        return []

    entries: list[Entry] = []
    for chunk in content.split(SEPARATOR):
        chunk = chunk.strip()
        if not chunk:
            continue
        entries.append(parse_entry(chunk, filepath.stem))
    return entries


def load_all_entries(config: dict) -> list[Entry]:
    base = topics_dir(config)
    if not base.exists():
        return []

    entries: list[Entry] = []
    for filepath in sorted(base.glob("*.md")):
        entries.extend(load_topic_entries(filepath))
    return entries
