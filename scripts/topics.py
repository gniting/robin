#!/usr/bin/env python3
"""
topics.py — List all Robin topics

Usage:
  python3 topics.py         # List all topics with stats
  python3 topics.py --json  # Output as JSON
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from robin.cli import topics_main


def main():
    topics_main()


if __name__ == "__main__":
    main()
