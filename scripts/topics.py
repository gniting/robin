#!/usr/bin/env python3
"""
topics.py — List all Robin topics

Usage:
  python3 topics.py         # List all topics with stats
  python3 topics.py --json  # Output as JSON
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from robin.config import load_config, load_index
from robin.parser import load_all_entries


def main():
    parser = argparse.ArgumentParser(description="List all Robin topics")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    config = load_config()
    index = load_index(config)
    entries = load_all_entries(config)

    topics: dict[str, dict] = {}
    for entry in entries:
        topic_stats = topics.setdefault(
            entry.topic,
            {"topic": entry.topic, "filename": f"{entry.topic}.md", "entries": 0, "rated": 0, "unrated": 0},
        )
        topic_stats["entries"] += 1
        if index.get("items", {}).get(entry.entry_id, {}).get("rating") is None:
            topic_stats["unrated"] += 1
        else:
            topic_stats["rated"] += 1

    ordered_topics = [topics[key] for key in sorted(topics)]

    if args.json:
        print(json.dumps(ordered_topics, indent=2))
        return

    if not ordered_topics:
        print("No topics yet. Start filing things with Robin!")
        return

    total_entries = sum(topic["entries"] for topic in ordered_topics)
    print(f"{len(ordered_topics)} topics, {total_entries} total entries\n")
    for topic in ordered_topics:
        stars = "★" * topic["rated"] + "☆" * topic["unrated"] if topic["rated"] or topic["unrated"] else ""
        print(f"  {topic['topic']}")
        print(f"    {topic['entries']} entries  {stars}")
        print()


if __name__ == "__main__":
    main()
