#!/usr/bin/env python3
"""
review.py — Robin review script

Usage:
  python3 review.py                    # Pick and print best candidate
  python3 review.py --rate ID 5        # Rate an item (overwrites previous)
  python3 review.py --status           # Show review stats without surfacing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from robin.config import load_config, load_index, save_index
from robin.parser import load_all_entries
from robin.review_logic import pick_best_candidate, rate_item


def show_status(index: dict, config: dict) -> None:
    total = len(index.get("items", {}))
    rated = sum(1 for item in index.get("items", {}).values() if item.get("rating") is not None)
    unrated = total - rated
    min_items = config.get("min_items_before_review", 30)

    print("Review status:")
    print(f"  Total items:   {total}")
    print(f"  Rated:         {rated}")
    print(f"  Unrated:       {unrated}")
    print(f"  Min to review: {min_items}")
    print(f"  Ready:         {'YES' if total >= min_items else 'NO'}")


def main():
    parser = argparse.ArgumentParser(description="Robin review system")
    parser.add_argument("--status", action="store_true", help="Show review status")
    parser.add_argument("--rate", nargs=2, metavar=("ID", "RATING"), help="Rate an item by stable entry id")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    config = load_config()
    index = load_index(config)
    entries = load_all_entries(config)

    if args.rate:
        entry_id, rating = args.rate
        try:
            item = rate_item(index, entry_id, int(rating))
        except KeyError:
            print(f"ERROR: Item '{entry_id}' not found in index")
            sys.exit(1)
        except ValueError as exc:
            print(f"ERROR: {exc}")
            sys.exit(1)
        save_index(index)
        if args.json:
            print(json.dumps(item, indent=2))
            return
        print(f"✓ Rated {entry_id}: {item['rating']}/5")
        return

    if args.status:
        if args.json:
            total = len(index.get("items", {}))
            rated = sum(1 for item in index.get("items", {}).values() if item.get("rating") is not None)
            print(json.dumps({
                "total_items": total,
                "rated": rated,
                "unrated": total - rated,
                "min_items_before_review": config.get("min_items_before_review", 30),
                "ready": total >= config.get("min_items_before_review", 30),
            }, indent=2))
            return
        show_status(index, config)
        return

    total = len(index.get("items", {}))
    min_items = config.get("min_items_before_review", 30)
    if total < min_items:
        print(f"SKIP: {total} items (need {min_items})")
        return

    candidate = pick_best_candidate(index, entries, config)
    if candidate is None:
        print("SKIP: No eligible items (all recently surfaced or not indexed)")
        return

    item, entry = candidate
    if args.json:
        print(json.dumps({
            "id": entry.entry_id,
            "topic": entry.topic,
            "date_added": entry.date_added,
            "source": entry.source,
            "tags": entry.tags,
            "body": entry.body,
            "rating": item.get("rating"),
            "times_surfaced": item.get("times_surfaced", 0),
        }, indent=2))
        return

    print(f"[{entry.topic}.md] {entry.entry_id}")
    print(
        f"Date: {entry.date_added} | Rating: {item.get('rating') or 'unrated'} | "
        f"Surfaced: {item.get('times_surfaced', 0)}x"
    )
    if entry.tags:
        print(f"Tags: {', '.join(entry.tags)}")
    print()
    print(entry.body)
    print()
    print(f"→ To rate: python3 review.py --rate \"{entry.entry_id}\" <1-5>")


if __name__ == "__main__":
    main()
