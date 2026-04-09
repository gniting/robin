#!/usr/bin/env python3
"""
search.py — Search Robin's commonplace book

Usage:
  python3 search.py <query>           # Search entry bodies and sources
  python3 search.py --topic <name>    # List all entries in a topic
  python3 search.py --tags tag1,tag2  # Find entries with these tags
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from robin.cli import search_main


def main():
    search_main()


if __name__ == "__main__":
    main()
