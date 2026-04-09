from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from robin.config import load_config, load_index, save_index
from robin.index import ensure_entry_in_index, rebuild_index
from robin.media import copy_image_to_vault, is_video_url
from robin.parser import SEPARATOR, load_all_entries, topic_slug, topic_to_filename, topics_dir
from robin.review_logic import pick_best_candidate, rate_item
from robin.search_logic import filter_by_tags, filter_by_topic, search_entries
from robin.serializer import build_media_entry, build_text_entry, generate_entry_id, serialize_entry


def _error(message: str, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps({"error": message}, indent=2))
    else:
        print(f"ERROR: {message}")
    raise SystemExit(1)


def _add_to_topic(config: dict, topic: str, entry_text: str) -> str:
    base = topics_dir(config)
    base.mkdir(parents=True, exist_ok=True)
    filepath = base / topic_to_filename(topic)

    if filepath.exists():
        content = filepath.read_text(encoding="utf-8").rstrip()
        out = content + SEPARATOR + entry_text
    else:
        out = entry_text

    filepath.write_text(out + "\n", encoding="utf-8")
    return filepath.name


def add_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Add an entry to Robin's commonplace book")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--entry-type", choices=["text", "image", "video"], default="text", help="Entry type")
    parser.add_argument("--content", default="", help="Content to file")
    parser.add_argument("--description", required=True, help="2-3 sentence context to store with the entry")
    parser.add_argument("--source", help="Source URL")
    parser.add_argument("--media-path", help="Local image file path for image entries")
    parser.add_argument("--media-url", help="Remote video URL for video entries")
    parser.add_argument("--creator", help="Required for media entries")
    parser.add_argument("--published-at", help="Required for media entries")
    parser.add_argument("--summary", help="Required for media entries")
    parser.add_argument("--note", help="Robin note")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args(argv)

    config = load_config()
    index = load_index()

    topic = args.topic.strip()
    date_added = str(date.today())
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    entry_type = args.entry_type

    if entry_type == "text":
        if not args.content.strip():
            _error("Text entries require --content.", as_json=args.json)
        entry = build_text_entry(
            topic=topic,
            content=args.content.strip(),
            description=args.description.strip(),
            source=args.source.strip() if args.source else None,
            note=args.note.strip() if args.note else None,
            tags=tags,
            date_added=date_added,
        )
    else:
        missing = [
            flag
            for flag, value in (
                ("--creator", args.creator),
                ("--published-at", args.published_at),
                ("--summary", args.summary),
            )
            if not (value or "").strip()
        ]
        if missing:
            _error(f"Media entries require {', '.join(missing)}.", as_json=args.json)

        entry_id = generate_entry_id(date_added)
        if entry_type == "image":
            if not args.media_path:
                _error("Image entries require --media-path.", as_json=args.json)
            if args.media_url:
                _error("Image entries do not accept --media-url.", as_json=args.json)
            try:
                media_source = copy_image_to_vault(config, topic, entry_id, args.media_path)
            except ValueError as exc:
                _error(str(exc), as_json=args.json)
            except OSError as exc:
                _error(f"Failed to copy image into vault: {exc}", as_json=args.json)
        else:
            if args.media_path:
                _error("Uploaded or local video files are not supported. Pass a video URL with --media-url.", as_json=args.json)
            if not args.media_url:
                _error("Video entries require --media-url.", as_json=args.json)
            if not is_video_url(args.media_url):
                _error("Video entries require a valid http(s) URL.", as_json=args.json)
            media_source = args.media_url.strip()

        entry = build_media_entry(
            topic=topic,
            media_kind=entry_type,
            media_source=media_source,
            description=args.description.strip(),
            creator=args.creator.strip(),
            published_at=args.published_at.strip(),
            summary=args.summary.strip(),
            content=args.content.strip(),
            source=args.source.strip() if args.source else None,
            note=args.note.strip() if args.note else None,
            tags=tags,
            date_added=date_added,
            entry_id=entry_id,
        )

    filename = _add_to_topic(config, topic, serialize_entry(entry))
    ensure_entry_in_index(entry, index)
    save_index(index)

    if args.json:
        print(
            json.dumps(
                {
                    "id": entry.entry_id,
                    "topic": entry.topic,
                    "filename": filename,
                    "entry_type": entry.entry_type,
                    "media_source": entry.media_source,
                    "description": entry.description,
                },
                indent=2,
            )
        )
        return

    print(f"✓ Filed {entry.entry_id} under [{topic}]({filename})")


def review_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Robin review system")
    parser.add_argument("--status", action="store_true", help="Show review status")
    parser.add_argument("--rate", nargs=2, metavar=("ID", "RATING"), help="Rate an item by stable entry id")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args(argv)

    config = load_config()
    index = load_index()

    if args.rate:
        entry_id, rating = args.rate
        try:
            rating_value = int(rating)
        except ValueError:
            print("ERROR: Rating must be a number between 1 and 5.")
            sys.exit(1)
        try:
            item = rate_item(index, entry_id, rating_value)
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
        total = len(index.get("items", {}))
        rated = sum(1 for item in index.get("items", {}).values() if item.get("rating") is not None)
        if args.json:
            print(json.dumps({
                "total_items": total,
                "rated": rated,
                "unrated": total - rated,
                "min_items_before_review": config.get("min_items_before_review", 30),
                "ready": total >= config.get("min_items_before_review", 30),
            }, indent=2))
            return
        print("Review status:")
        print(f"  Total items:   {total}")
        print(f"  Rated:         {rated}")
        print(f"  Unrated:       {total - rated}")
        print(f"  Min to review: {config.get('min_items_before_review', 30)}")
        print(f"  Ready:         {'YES' if total >= config.get('min_items_before_review', 30) else 'NO'}")
        return

    total = len(index.get("items", {}))
    min_items = config.get("min_items_before_review", 30)
    if total < min_items:
        print(f"SKIP: {total} items (need {min_items})")
        return

    entries = load_all_entries(config)
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
            "entry_type": entry.entry_type,
            "media_kind": entry.media_kind,
            "media_source": entry.media_source,
            "source": entry.source,
            "description": entry.description,
            "creator": entry.creator,
            "published_at": entry.published_at,
            "summary": entry.summary,
            "tags": entry.tags,
            "body": entry.body,
            "rating": item.get("rating"),
            "times_surfaced": item.get("times_surfaced", 0),
        }, indent=2))
        return

    print(f"[{entry.topic}.md] {entry.entry_id}")
    print(f"Date: {entry.date_added} | Rating: {item.get('rating') or 'unrated'} | Surfaced: {item.get('times_surfaced', 0)}x")
    if entry.entry_type != "text":
        print(f"Type: {entry.entry_type}")
    if entry.media_source:
        print(f"Media: {entry.media_source}")
    if entry.creator:
        print(f"Creator: {entry.creator}")
    if entry.published_at:
        print(f"Published: {entry.published_at}")
    if entry.summary:
        print(f"Summary: {entry.summary}")
    if entry.tags:
        print(f"Tags: {', '.join(entry.tags)}")
    if entry.description:
        print(f"Description: {entry.description}")
    print()
    print(entry.body)
    print()
    print(f"→ To rate: python3 review.py --rate \"{entry.entry_id}\" <1-5>")


def search_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Search Robin's commonplace book")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--topic", help="Filter by topic name")
    parser.add_argument("--tags", help="Comma-separated tag filter")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args(argv)

    config = load_config()
    index = load_index()
    entries = load_all_entries(config)

    if args.topic:
        entries = filter_by_topic(entries, topic_slug(args.topic))
        heading = f"Topic '{args.topic}': {len(entries)} entries"
    elif args.tags:
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        if not tags:
            print("ERROR: Provide at least one non-empty tag.")
            sys.exit(1)
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
                    "entry_type": entry.entry_type,
                    "media_kind": entry.media_kind,
                    "media_source": entry.media_source,
                    "source": entry.source,
                    "description": entry.description,
                    "creator": entry.creator,
                    "published_at": entry.published_at,
                    "summary": entry.summary,
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
        rating = index.get("items", {}).get(entry.entry_id, {}).get("rating")
        print(f"[{entry.topic}.md] {entry.entry_id} / {entry.date_added}  ★{rating or '—'}")
        if entry.entry_type != "text":
            print(f"  Type: {entry.entry_type}")
        if entry.media_source:
            print(f"  Media: {entry.media_source}")
        if entry.source:
            print(f"  Source: {entry.source}")
        if entry.creator:
            print(f"  Creator: {entry.creator}")
        if entry.published_at:
            print(f"  Published: {entry.published_at}")
        if entry.summary:
            print(f"  Summary: {entry.summary}")
        if entry.description:
            print(f"  Description: {entry.description}")
        if entry.tags:
            print(f"  Tags: {', '.join(entry.tags)}")
        body = entry.body.replace("\n", " ").strip()
        print(f"  {body[:200]}{'...' if len(body) > 200 else ''}")
        print()


def topics_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="List all Robin topics")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args(argv)

    config = load_config()
    index = load_index()
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
        rated_visual = min(topic["rated"], 10)
        unrated_visual = min(max(10 - rated_visual, 0), topic["unrated"])
        stars = "★" * rated_visual + "☆" * unrated_visual
        print(f"  {topic['topic']}")
        print(f"    {topic['entries']} entries  {stars}  {topic['rated']} rated / {topic['unrated']} unrated")
        print()


def reindex_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rebuild Robin's review index")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args(argv)

    config = load_config()
    old_index = load_index()
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
    print(f"✓ Index rebuilt: {len(new_index['items'])} items, {rated} rated, {len(new_index['items']) - rated} unrated")
