#!/usr/bin/env python3
"""
reindex.py — Rebuild Robin's review index from topic files

Usage:
  python3 reindex.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from robin.config import load_config, load_index, save_index
from robin.index import rebuild_index
from robin.parser import load_all_entries


def main():
    parser = argparse.ArgumentParser(description="Rebuild Robin's review index")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    config = load_config()
    old_index = load_index(config)
    entries = load_all_entries(config)
    new_index = rebuild_index(entries, old_index)
    save_index(new_index)

    rated = sum(1 for item in new_index["items"].values() if item.get("rating") is not None)
    if args.json:
        print(json.dumps({
            "entries_found": len(entries),
            "items_indexed": len(new_index["items"]),
            "rated": rated,
            "unrated": len(new_index["items"]) - rated,
        }, indent=2))
        return

    print("Scanning topic files...")
    print(f"Found {len(entries)} entries")
    print(
        f"✓ Index rebuilt: {len(new_index['items'])} items, "
        f"{rated} rated, {len(new_index['items']) - rated} unrated"
    )


if __name__ == "__main__":
    main()
