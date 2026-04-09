#!/usr/bin/env python3
"""
review.py — Robin review script

Usage:
  python3 review.py                    # Pick and print best candidate
  python3 review.py --rate ID 5        # Rate an item (overwrites previous)
  python3 review.py --status           # Show review stats without surfacing
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from robin.cli import review_main


def main():
    review_main()


if __name__ == "__main__":
    main()
