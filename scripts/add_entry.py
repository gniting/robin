#!/usr/bin/env python3
"""
add_entry.py — Robin add entry script

Usage:
  python3 add_entry.py --topic "AI Reasoning" --content "..." [--source URL] [--note "..."] [--tags tag1,tag2]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from robin.config import load_config, load_index, save_index
from robin.index import ensure_entry_in_index
from robin.parser import SEPARATOR, topic_to_filename, topics_dir
from robin.serializer import build_entry, serialize_entry


def add_to_topic(config: dict, topic: str, entry_text: str) -> str:
    base = topics_dir(config)
    base.mkdir(parents=True, exist_ok=True)
    filepath = base / topic_to_filename(topic)

    if filepath.exists():
        content = filepath.read_text().rstrip()
        out = content + SEPARATOR + entry_text
    else:
        out = entry_text

    filepath.write_text(out + "\n")
    return filepath.name


def main():
    parser = argparse.ArgumentParser(description="Add an entry to Robin's commonplace book")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--content", required=True, help="Content to file")
    parser.add_argument("--source", help="Source URL")
    parser.add_argument("--note", help="Robin note")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    config = load_config()
    index = load_index(config)

    topic = args.topic.strip()
    date_added = str(date.today())
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]

    entry = build_entry(
        topic=topic,
        content=args.content.strip(),
        source=args.source.strip() if args.source else None,
        note=args.note.strip() if args.note else None,
        tags=tags,
        date_added=date_added,
    )

    filename = add_to_topic(config, topic, serialize_entry(entry))
    ensure_entry_in_index(entry, index)
    save_index(index)

    if args.json:
        print(json.dumps({"id": entry.entry_id, "topic": entry.topic, "filename": filename}, indent=2))
        return

    print(f"✓ Filed {entry.entry_id} under [{topic}]({filename})")


if __name__ == "__main__":
    main()
