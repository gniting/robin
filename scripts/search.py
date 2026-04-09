#!/usr/bin/env python3
"""
search.py — Search Robin's commonplace book

Usage:
  python3 search.py <query>           # Search entry bodies and sources
  python3 search.py --topic <name>    # List all entries in a topic
  python3 search.py --tags tag1,tag2  # Find entries with these tags
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from robin.config import load_config, load_index
from robin.parser import load_all_entries
from robin.search_logic import filter_by_tags, filter_by_topic, search_entries


def print_entry(entry, index: dict) -> None:
    rating = index.get("items", {}).get(entry.entry_id, {}).get("rating")
    print(f"[{entry.topic}.md] {entry.entry_id} / {entry.date_added}  ★{rating or '—'}")
    if entry.source:
        print(f"  Source: {entry.source}")
    if entry.tags:
        print(f"  Tags: {', '.join(entry.tags)}")
    body = entry.body.replace("\n", " ").strip()
    print(f"  {body[:200]}{'...' if len(body) > 200 else ''}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Search Robin's commonplace book")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--topic", help="Filter by topic name")
    parser.add_argument("--tags", help="Comma-separated tag filter")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    config = load_config()
    index = load_index(config)
    entries = load_all_entries(config)

    if args.topic:
        entries = filter_by_topic(entries, args.topic)
        heading = f"Topic '{args.topic}': {len(entries)} entries"
    elif args.tags:
        tags = [tag.strip() for tag in args.tags.split(",")]
        entries = filter_by_tags(entries, tags)
        heading = f"Tags [{', '.join(tags)}]: {len(entries)} results"
    elif args.query:
        entries = search_entries(entries, args.query)
        heading = f"Query '{args.query}': {len(entries)} results"
    else:
        heading = f"Total: {len(entries)} entries"

    if args.json:
        print(json.dumps({
            "count": len(entries),
            "entries": [
                {
                    "id": entry.entry_id,
                    "topic": entry.topic,
                    "date_added": entry.date_added,
                    "source": entry.source,
                    "tags": entry.tags,
                    "rating": index.get("items", {}).get(entry.entry_id, {}).get("rating"),
                    "body": entry.body,
                }
                for entry in entries
            ],
        }, indent=2))
        return

    print(heading)
    print()
    for entry in entries:
        print_entry(entry, index)


if __name__ == "__main__":
    main()
