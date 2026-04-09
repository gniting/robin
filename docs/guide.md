# Robin Guide

This guide is for advanced users who want manual control over Robin: state-directory setup, config files, CLI usage, file layout, and troubleshooting.

## Storage Model

Robin separates user content from Robin state.

Recommended layout:

```text
agent-workspace/
  data/
    robin/
      robin-config.json
      robin-review-index.json

vault_path/
  media/
    poetry/
      20260409-a1f3c9.png
  topics/
    reasoning.md
    poetry.md
    quotes.md
```

- The vault stores user-facing content.
- The Robin state directory stores config and review metadata.
- Robin does not guess where its state lives.

## Runtime Contract

Every Robin command needs a state directory.

Robin accepts both:

- `--state-dir /path/to/data/robin`
- `ROBIN_STATE_DIR=/path/to/data/robin`

Precedence:

1. `--state-dir`
2. `ROBIN_STATE_DIR`
3. otherwise Robin exits with an error

Expected files inside the state directory:

- `robin-config.json`
- optionally `robin-review-index.json`

If neither `--state-dir` nor `ROBIN_STATE_DIR` is present, Robin exits with:

```text
Robin state directory is not configured. Pass --state-dir or set ROBIN_STATE_DIR.
```

## Manual Setup

Create a state directory:

```bash
mkdir -p /path/to/agent-workspace/data/robin
mkdir -p /path/to/your/vault/topics
mkdir -p /path/to/your/vault/media
```

Create `/path/to/agent-workspace/data/robin/robin-config.json`:

```json
{
  "vault_path": "/path/to/your/vault",
  "topics_dir": "topics",
  "media_dir": "media",
  "min_items_before_review": 30,
  "review_cooldown_days": 60
}
```

`vault_path` is the only required config field. The remaining fields are optional and default to:

- `topics_dir`: `topics`
- `media_dir`: `media`
- `min_items_before_review`: `30`
- `review_cooldown_days`: `60`

Optional: create `/path/to/agent-workspace/data/robin/robin-review-index.json`:

```json
{
  "items": {}
}
```

If the file is missing, Robin starts with an empty in-memory index and writes it when needed.

Then either export the state dir:

```bash
export ROBIN_STATE_DIR=/path/to/agent-workspace/data/robin
```

Or pass it explicitly on each command:

```bash
python3 scripts/topics.py --state-dir /path/to/agent-workspace/data/robin
```

This is also the simplest setup verification step. A healthy empty setup returns `No topics yet. Start filing things with Robin!`

## Topic Files

Robin stores content in topic-organized Markdown files under `topics/`.

Topic filenames use lowercase slugs with non-alphanumeric characters normalized to dashes.

Examples:

- `Song Lyrics` -> `song-lyrics.md`
- `AI/ML` -> `ai-ml.md`

Entries are separated by `***`. Each entry has frontmatter, then a blank line, then the body.

Text example:

```text
id: 20260408-a1f3c9
date_added: 2026-04-08
description: A short excerpt from a Paul Graham essay about optimizing for what matters. Useful as a general reminder when making tradeoff decisions.
source: https://example.com/article
tags: [ai, reasoning]

Notable excerpt or the thing you sent.
```

Image example:

```text
id: 20260408-b7k2d1
date_added: 2026-04-08
entry_type: image
media_kind: image
media_source: media/poetry/20260408-b7k2d1.png
description: A photographed poem excerpt worth revisiting for tone and imagery.
creator: Mary Oliver
published_at: 1986
summary: An excerpt about attention and observation in everyday life.
tags: [poetry]

Opening lines from the photographed page.
```

Field meanings:

- `id`: stable entry identifier
- `date_added`: entry date
- `entry_type`: `text`, `image`, or `video`
- `media_kind`: same as `entry_type` for media entries; omitted for text entries
- `media_source`: copied relative path for images or external URL for videos
- `source`: original source URL when available
- `description`: required context for every entry
- `creator`, `published_at`, `summary`: required for media entries
- `tags`: optional tag list

## Media Rules

Robin accepts media with these rules:

- local image files: accepted and copied into the vault media directory
- remote image URLs: not supported directly by Robin's CLI
- video URLs: accepted and stored by reference
- uploaded or local video files: rejected

Robin will not store a media entry unless the caller provides:

- `description`
- `creator`
- `published_at`
- `summary`

If a media item is rejected, Robin stores nothing and returns an error.

Robin also rejects any entry whose serialized body would contain a standalone `***` line, because `***` is Robin's internal entry separator.

## Search: Host Index vs Robin Search

If your agent supports file indexing, it should index Robin topic files like any other Markdown content.

Use host/global search for:

- broad semantic recall across all user content
- exploratory queries where Robin may be only one source

Use `robin-search` for:

- Robin-specific lookup
- topic filtering
- tag filtering
- deterministic lookup of Robin entries
- structured JSON output with stable ids, metadata, and ratings
- fallback when host indexing is unavailable or stale

`robin-search` can combine filters. If both `--topic` and `--tags` are provided, Robin first narrows to the topic and then applies the tag filter within that topic.

## CLI Reference

Installed entry points:

- `robin-add`
- `robin-review`
- `robin-reindex`
- `robin-search`
- `robin-topics`

Repo-local equivalents:

- `python3 scripts/add_entry.py`
- `python3 scripts/review.py`
- `python3 scripts/reindex.py`
- `python3 scripts/search.py`
- `python3 scripts/topics.py`

All Robin commands support `--state-dir`.

Recommended path for agents:

- run the repo-local `python3 scripts/*.py` commands directly

Optional path for advanced users:

- `pip install -e .`
- then use the installed `robin-add`, `robin-review`, `robin-reindex`, `robin-search`, and `robin-topics` entry points

Examples:

```bash
python3 scripts/search.py --state-dir /path/to/data/robin "clear thinking" --json
python3 scripts/review.py --state-dir /path/to/data/robin --json
python3 scripts/review.py --state-dir /path/to/data/robin --status --json
python3 scripts/review.py --state-dir /path/to/data/robin --rate 20260408-a1f3c9 5
python3 scripts/review.py --state-dir /path/to/data/robin --rate 20260408-a1f3c9 5 --json
python3 scripts/search.py --state-dir /path/to/data/robin --topic "AI Reasoning" --json
python3 scripts/search.py --state-dir /path/to/data/robin --tags "writing,clarity" --json
python3 scripts/search.py --state-dir /path/to/data/robin --topic "AI Reasoning" --tags "clarity" --json
python3 scripts/topics.py --state-dir /path/to/data/robin --json
python3 scripts/add_entry.py --state-dir /path/to/data/robin --topic "reasoning" --content "The most important thing is to decide what you are optimizing for." --description "A short Paul Graham line about choosing the objective before optimizing. Useful when reviewing tradeoff-heavy decisions." --json
python3 scripts/add_entry.py --state-dir /path/to/data/robin --topic "writing" --content "Write as if speaking to a smart friend." --description "A reminder to keep prose conversational and clear." --source "https://example.com/article" --note "Pair this with other writing advice." --json
python3 scripts/add_entry.py --state-dir /path/to/data/robin --topic "reasoning" --content "The map is not the territory." --description "A reminder that abstractions are not reality itself." --tags "thinking,quotes" --json
python3 scripts/add_entry.py --state-dir /path/to/data/robin --entry-type image --topic "poetry" --media-path ~/Downloads/poem.png --description "A photographed poem excerpt worth revisiting." --creator "Mary Oliver" --published-at "1986" --summary "An excerpt about attention and observation." --json
python3 scripts/add_entry.py --state-dir /path/to/data/robin --entry-type video --topic "talks" --media-url "https://www.youtube.com/watch?v=abc123" --description "A talk to revisit for its framing and examples." --creator "Speaker Name" --published-at "2025-01-01" --summary "A concise summary of the talk." --json
python3 scripts/reindex.py --state-dir /path/to/data/robin
```

The examples above use the repo-local `python3 scripts/*.py` path. If you installed the package with `pip install -e .`, the `robin-*` entry points are equivalent aliases.

All CLI helpers support `--json`.

Use `python3 scripts/reindex.py --state-dir <state-dir>` after manual edits to topic files, when rebuilding review state from existing markdown, or when importing legacy entries and wanting the review index rebuilt from disk.

## Review System

Robin maintains a review index keyed by entry `id`. It stores:

- `rating`
- `last_surfaced`
- `times_surfaced`

Review behavior:

1. Robin waits until there are at least `min_items_before_review` items.
2. It prefers unrated items first.
3. Then lower-rated items.
4. Then items with the fewest total prior surfaces.
5. It skips items surfaced within `review_cooldown_days`.
6. When Robin surfaces an item, it immediately increments `times_surfaced`, sets `last_surfaced`, and marks `_awaiting_rating` as `true`.
7. A subsequent `--rate` call for that surfaced item overwrites the previous rating and sets `_awaiting_rating` back to `false` without incrementing `times_surfaced` again.

If `--rate` is called directly on an item that was not surfaced first, Robin still sets `last_surfaced`, increments `times_surfaced`, and keeps `_awaiting_rating` as `false`.

Example index shape:

```json
{
  "items": {
    "20260408-a1f3c9": {
      "id": "20260408-a1f3c9",
      "topic": "ai-reasoning",
      "date": "2026-04-08",
      "rating": null,
      "last_surfaced": "2026-04-08T10:00:00+00:00",
      "times_surfaced": 0,
      "_awaiting_rating": false
    }
  }
}
```

`_awaiting_rating` is an internal review-state flag. It is `true` after Robin surfaces an item and becomes `false` again after that surface is rated.

## Troubleshooting

- Config not found:
  Create `robin-config.json` in the state directory and pass `--state-dir` or set `ROBIN_STATE_DIR`.
- Review index not found:
  Robin can start without it. If you want to create it manually, use `{"items": {}}`.
- Media entry rejected:
  Ensure the caller provided `description`, `creator`, `published_at`, and `summary`.
- Image copy failed:
  Confirm the local image path exists and the vault `media/` directory is writable.
