---
name: robin
description: Save and review notes, quotes, articles, links, images, and video references in a personal commonplace book. Use when the user wants to file something to remember, organize knowledge by topic, resurface saved items, or review prior entries.
license: MIT
compatibility: Requires Python 3.11+ and local filesystem access. Optional: a scheduler for periodic review.
metadata:
  category: personal
---

# Robin — Personal Knowledge Curation Skill

Robin is a digital commonplace book. The user gives content to the AI agent, and the agent uses Robin to store it in topic-organized Markdown files and resurface it later for review.

## Storage Model

- `vault_path` is the user content vault
- `vault_path/topics/` stores topic-organized Markdown files
- `vault_path/media/` stores copied image assets
- the Robin state directory stores:
  - `robin-config.json`
  - optionally `robin-review-index.json`

Recommended default state directory:

- `<agent-workspace>/data/robin/`

Robin does not guess host layout. The caller must provide the Robin state directory explicitly.

## Host Requirements

The host agent must be able to:

- read and write local files
- run bundled Python scripts
- pass CLI arguments or environment variables to Robin
- schedule periodic review if review automation is desired

## Setup Contract

The host agent is responsible for first-run setup.

On setup, the agent should:

1. choose a state directory, usually `<agent-workspace>/data/robin/`
2. create the state directory if it does not exist
3. create `robin-config.json` in that directory if it does not exist
4. ensure the configured vault contains `topics/` and `media/`
5. optionally create `robin-review-index.json`; Robin will create an empty in-memory index if it is missing
6. verify setup by running `python3 scripts/topics.py --state-dir <state-dir>`

Example `robin-config.json`:

```json
{
  "vault_path": "/path/to/your/vault",
  "topics_dir": "topics",
  "media_dir": "media",
  "min_items_before_review": 30,
  "review_cooldown_days": 60
}
```

`vault_path` is the only required config field. If omitted, Robin cannot run. All other config fields have defaults:

- `topics_dir`: `topics`
- `media_dir`: `media`
- `min_items_before_review`: `30`
- `review_cooldown_days`: `60`

Optional example `robin-review-index.json`:

```json
{
  "items": {}
}
```

## Runtime Contract

Robin accepts both:

- `--state-dir /path/to/data/robin`
- `ROBIN_STATE_DIR=/path/to/data/robin`

Precedence:

1. `--state-dir`
2. `ROBIN_STATE_DIR`
3. otherwise fail

If neither is provided, Robin exits with:

```text
Robin state directory is not configured. Pass --state-dir or set ROBIN_STATE_DIR.
```

Default runnable path:

- agents can run the repo-local scripts directly without installing the package:
  - `python3 scripts/add_entry.py`
  - `python3 scripts/review.py`
  - `python3 scripts/reindex.py`
  - `python3 scripts/search.py`
  - `python3 scripts/topics.py`

Optional installed path:

- if the agent runs `pip install -e .`, Robin also exposes:
  - `robin-add`
  - `robin-review`
  - `robin-reindex`
  - `robin-search`
  - `robin-topics`

For advanced manual setup details and shell examples, see [docs/guide.md](docs/guide.md).

## Agent Responsibilities

When using Robin, the agent is responsible for:

- choosing the topic
- deciding whether the entry is `text`, `image`, or `video`
- generating a useful `description` for every entry
- generating `creator`, `published_at`, and `summary` for every media entry
- refusing to store media if the required metadata is missing
- passing only supported media forms to Robin:
  - local image file paths for images
  - `http(s)` URLs for videos
  - never uploaded or local video files
- passing `--state-dir` or `ROBIN_STATE_DIR` on every Robin invocation

Robin is responsible for:

- persisting the entry and copied image assets
- preserving stable ids
- resurfacing the stored text, media reference, and metadata later
- maintaining review state
- returning a clear error instead of storing incomplete or unsupported media entries

## Safety Boundary

Robin is a storage and retrieval skill, not a code-editing skill.

Normal Robin use may:

- write to the configured vault
- update the review index
- copy accepted image assets into the vault media directory

Normal Robin use must not:

- modify Robin's source code
- modify Robin's docs
- change packaging or tests
- change the skill implementation unless the user explicitly asks to edit Robin itself

If the agent notices a Robin bug while using the skill, it should report the issue to the user instead of patching Robin unless the user explicitly asks for a fix.

## Filing

1. The user sends content to the AI agent.
2. The agent scans existing topic files and picks the best match.
3. If confident, the agent files the item and confirms.
4. If unsure between topics, the agent asks the user to choose.
5. If no match exists, the agent suggests a new topic, files the item, and flags it for review.
6. For media items, the agent must also supply `creator`, `published_at`, and `summary`. If any are missing, Robin rejects the entry.

### Entry-Type Rules

- `text`
  - requires: `topic`, `content`, `description`
  - optional: `source`, `note`, `tags`
- `image`
  - requires: `topic`, local image file path, `description`, `creator`, `published_at`, `summary`
  - optional: `content`, `source`, `note`, `tags`
  - behavior: Robin copies the image into `vault_path/media/`
- `video`
  - requires: `topic`, video URL, `description`, `creator`, `published_at`, `summary`
  - optional: `content`, `source`, `note`, `tags`
  - behavior: Robin stores the URL only
  - rejection: local or uploaded video files are always rejected

### Failure Rules

Robin rejects the add operation if:

- a text entry is missing `content`
- a media entry is missing `description`, `creator`, `published_at`, or `summary`
- an image entry is missing a local file path
- an image path does not exist or is not a supported image type
- a video entry is missing a valid `http(s)` URL
- a local or uploaded video file is supplied
- the serialized entry would contain a standalone `***` line, which Robin reserves as its internal entry separator

When the add operation fails, the agent should pass the returned error back to the user instead of pretending the item was stored.

## Review Mode

Review is host-triggered. Robin itself does not run a scheduler.

Review behavior:

1. Wait until `len(items) >= min_items_before_review`
2. Prefer unrated items first
3. Then lower-rated items
4. Then least frequently surfaced items
5. Skip items surfaced within `review_cooldown_days`
6. Surface the chosen entry, including media metadata when present
7. When an item is surfaced, Robin immediately increments `times_surfaced`, sets `last_surfaced`, and marks `_awaiting_rating` as `true`
8. Accept a rating from 1 to 5
9. If `_awaiting_rating` is `true`, rating only overwrites the rating and clears `_awaiting_rating` back to `false`

If the agent calls `--rate` directly on an item that was not surfaced first, Robin still sets `last_surfaced`, increments `times_surfaced`, and leaves `_awaiting_rating` as `false`.

## Search Guidance

When the host supports file indexing, Robin topic files should be part of the host agent's searchable corpus.

Use host/global search for:

- broad semantic retrieval across the user's workspace
- natural-language recall where Robin may or may not be the relevant source

Use `robin-search` for:

- Robin-specific lookup tasks
- filtering by topic or tags
- returning stable Robin ids and metadata
- deterministic JSON output for Robin entries
- fallback when host indexing is unavailable or stale

`robin-search` can combine filters. If both `--topic` and `--tags` are provided, Robin first narrows to the topic and then applies the tag filter within that topic.

## Commands

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

All Robin commands accept:

- `--state-dir`

Examples:

The examples below use the repo-local `python3 scripts/*.py` path. The installed `robin-*` commands are equivalent aliases if the package has been installed.

- `python3 scripts/add_entry.py --state-dir /path/to/data/robin --topic "reasoning" --content "..." --description "..."`
- `python3 scripts/add_entry.py --state-dir /path/to/data/robin --topic "writing" --content "..." --description "..." --note "Useful for later review."`
- `python3 scripts/add_entry.py --state-dir /path/to/data/robin --topic "writing" --content "Write as if speaking to a smart friend." --description "A reminder to keep prose conversational and clear." --source "https://example.com/article" --json`
- `python3 scripts/add_entry.py --state-dir /path/to/data/robin --topic "reasoning" --content "The map is not the territory." --description "A reminder that abstractions are not reality itself." --tags "thinking,quotes"`
- `python3 scripts/review.py --state-dir /path/to/data/robin`
- `python3 scripts/review.py --state-dir /path/to/data/robin --json`
- `python3 scripts/review.py --state-dir /path/to/data/robin --status --json`
- `python3 scripts/review.py --state-dir /path/to/data/robin --rate 20260408-a1f3c9 5`
- `python3 scripts/review.py --state-dir /path/to/data/robin --rate 20260408-a1f3c9 5 --json`
- `python3 scripts/search.py --state-dir /path/to/data/robin "clear thinking" --json`
- `python3 scripts/search.py --state-dir /path/to/data/robin --topic "AI Reasoning" --json`
- `python3 scripts/search.py --state-dir /path/to/data/robin --tags "writing,clarity" --json`
- `python3 scripts/search.py --state-dir /path/to/data/robin --topic "AI Reasoning" --tags "clarity" --json`
- `python3 scripts/topics.py --state-dir /path/to/data/robin --json`
- `python3 scripts/reindex.py --state-dir /path/to/data/robin`

Use `python3 scripts/reindex.py --state-dir <state-dir>` after manual edits to topic files, when rebuilding review state from existing markdown, or when importing legacy entries and wanting the review index rebuilt from disk.

## JSON Contract

Add success shape includes:

- `id`
- `topic`
- `filename` (topic file basename only, for example `ai-reasoning.md`)
- `entry_type`
- `media_source`
- `description`

Review success payload:

- `{"status": "ok", "id": "...", "topic": "...", "date_added": "YYYY-MM-DD", "entry_type": "text|image|video", "media_kind": "image|video|\"\"", "media_source": "...|\"\"", "source": "...|\"\"", "description": "...", "creator": "...|\"\"", "published_at": "...|\"\"", "summary": "...|\"\"", "tags": [...], "body": "...", "rating": 1|2|3|4|5|null, "times_surfaced": N}`

Review rate success payload:

- `{"id": "...", "topic": "...", "date": "YYYY-MM-DD", "rating": 1|2|3|4|5, "last_surfaced": "ISO-8601 timestamp", "times_surfaced": N, "_awaiting_rating": false}`

Search success payload:

- `{"count": N, "entries": [{"id": "...", "topic": "...", "date_added": "YYYY-MM-DD", "entry_type": "text|image|video", "media_kind": "image|video|\"\"", "media_source": "...|\"\"", "source": "...|\"\"", "description": "...", "creator": "...|\"\"", "published_at": "...|\"\"", "summary": "...|\"\"", "tags": [...], "body": "...", "rating": 1|2|3|4|5|null}]}`

Topics success payload:

- `[{"topic": "...", "filename": "...", "entries": N, "rated": N, "unrated": N}]`

Reindex success payload:

- `{"entries_found": N, "items_indexed": N, "rated": N, "unrated": N}`

Review skip payloads:

- `{"status": "skip", "reason": "not_enough_items", "total_items": N, "min_items_before_review": N}`
- `{"status": "skip", "reason": "no_eligible_items"}`

Review status payload:

- `{"total_items": N, "rated": N, "unrated": N, "min_items_before_review": N, "ready": true|false}`

Failure shape:

- `{"error": "..."}`

Exit status on failure:

- `1`

## Topic File Format

Entries are separated by `***`. Each entry is a frontmatter block followed by a blank line and then the body text.

```text
id: 20260408-a1f3c9
date_added: 2026-04-08
entry_type: image
media_kind: image
media_source: media/poetry/20260408-a1f3c9.png
description: A photographed poem excerpt worth revisiting.
creator: Mary Oliver
published_at: 1986
summary: An excerpt about attention and observation.
tags: [poetry]

Opening lines from the photographed page.
```

Topic filename: lowercase topic slug with non-alphanumeric characters normalized to dashes.

Frontmatter parsing rules:

- keys are matched case-insensitively
- a blank line must separate frontmatter from body
- body starts at the first blank line

## Review Index Schema

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

Review settings such as `min_items_before_review` and `review_cooldown_days` live only in `robin-config.json`.

`_awaiting_rating` is an internal review-state flag. It is `true` after Robin surfaces an item and becomes `false` again after that surface is rated.

## Pitfalls

- Do not use `---` as an entry separator. Use `***`.
- Uploaded or local video files are rejected.
- A blank line is required after frontmatter.
- Keep `id` stable when manually editing entries.
