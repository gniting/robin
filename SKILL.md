---
name: robin
description: Save and review notes, quotes, articles, links, images, and video references in a personal commonplace book. Use when the user wants to file something to remember, organize knowledge by topic, resurface saved items, or review prior entries.
license: MIT
compatibility: Requires Python 3.11+ and local filesystem access. Optional: a scheduler for periodic review.
metadata:
  category: personal
---

# Robin — Personal Knowledge Curation Skill

A digital commonplace book inspired by the 17th–19th century tradition of collecting quotes, ideas, and observations. You feed Robin things you want to remember — quotes, articles, links, thoughts, images, and video links — and it files them into topic-organized markdown files. Robin also runs a spaced-repetition review engine that surfaces items on a schedule so you reinforce learning over time.

Named for Robin Williams' portrayal of Sean Maguire in Good Will Hunting — a reminder that the tools we build to sharpen our words are worth building well.

## Core Concepts

- **Vault path**: where your Obsidian vault lives (local on the skill host)
- **Topic files**: one markdown file per topic, entries appended chronologically, separated by `***`, each with a compact stable `id`
- **Media directory**: copied image assets live under `vault_path/media/` by default
- **Review index**: stored under `data/robin/robin-review-index.json` in the agent workspace by default
- **Config**: stored under `data/robin/robin-config.json` in the agent workspace by default
- **Config example**: shipped in `references/robin-config.json.example` for first-run setup

## Host Compatibility

Robin is host-neutral.

- Preferred runtime root: the agent workspace under `data/robin/`
- Advanced overrides: `ROBIN_WORKSPACE`, `ROBIN_CONFIG_FILE`, `ROBIN_INDEX_FILE`, `ROBIN_HOME`
- Compatibility fallback: XDG or `HERMES_HOME/data` if no workspace-local state is discoverable
- Required host capabilities:
  - local filesystem access
  - ability to run bundled Python scripts
  - Python 3.11+
  - ability to invoke Robin on a schedule if periodic review is desired

## Safety Boundary

Robin is a storage and retrieval skill, not a code-editing skill.

During normal Robin use, I may:

- write entries into the user's vault
- copy accepted image assets into the user's vault media directory
- update the review index

During normal Robin use, I must not:

- edit Robin's source code, tests, docs, packaging, or install scripts
- change files inside the installed Robin skill directory
- modify `README.md`, `SKILL.md`, `install.sh`, `pyproject.toml`, or Python modules

If I notice a bug or packaging problem in Robin while using the skill, I should report it to the user instead of patching it, unless the user explicitly asks me to modify Robin itself.

## Agent Responsibilities

When using Robin, I am responsible for:

- choosing the topic
- deciding whether the entry is `text`, `image`, or `video`
- generating a useful `description` for every entry
- generating `creator`, `published_at`, and `summary` for every media entry
- refusing to store media if the required metadata is missing
- passing only supported media forms to Robin:
  - local image file paths for images
  - `http(s)` URLs for videos
  - never uploaded/local video files

Robin is responsible for:

- persisting the entry and copied image assets
- preserving stable ids
- resurfacing the stored text, media reference, and metadata later
- maintaining review state
- returning a clear error instead of storing incomplete or unsupported media entries

## Interaction Patterns

### Filing (default mode)

1. You send content (text, link, quote, note, article, image, or video link)
2. I scan existing topic files, pick the best match
3. If confident — file it and confirm
4. If unsure between two topics — ask you to choose
5. If no match exists — suggest a new topic name, file it, flag for review
6. For media items, I must also supply `creator`, `published_at`, and `summary`; if any are missing, Robin rejects the entry

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

Robin must reject the add operation if:

- a text entry is missing `content`
- a media entry is missing `description`, `creator`, `published_at`, or `summary`
- an image entry is missing a local file path
- an image path does not exist or is not a supported image type
- a video entry is missing a valid `http(s)` URL
- a local or uploaded video file is supplied

When the add operation fails, I should pass the returned error back to the user instead of pretending the item was stored.

### Review mode

Triggered by the review cron. Only runs when `items.count >= min_items_before_review`:

1. Pick the best candidate: unrated items first, then lowest rating, then least recently surfaced
2. Skip any item surfaced within `review_cooldown_days`
3. Surface the item to you with context, including media reference and metadata for media entries
4. You rate it 1–5
5. I update the review index — rating is always overwritten with the new one
6. Increment `times_surfaced`, set `last_surfaced`

### Commands

- `robin review` — manually trigger a review cycle
- `robin reindex` — rebuild review index from topic files (use after manual edits)
- `robin search <query>` — query Robin entries with topic/tag filters and structured Robin-aware results
- `robin topics` — list all existing topics
- `robin add` — file something new (can also just send content directly)
- `robin setup` — first-run config wizard

### Search Guidance

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

### CLI Contract

Repo-local scripts:

- `python3 scripts/add_entry.py`
- `python3 scripts/review.py`
- `python3 scripts/reindex.py`
- `python3 scripts/search.py`
- `python3 scripts/topics.py`

Installed entry points:

- `robin-add`
- `robin-review`
- `robin-reindex`
- `robin-search`
- `robin-topics`

Add-entry flags:

- common: `--topic`, `--entry-type`, `--description`, `--source`, `--note`, `--tags`, `--json`
- text: `--content`
- image: `--media-path`, `--creator`, `--published-at`, `--summary`
- video: `--media-url`, `--creator`, `--published-at`, `--summary`

JSON add success shape includes:

- `id`
- `topic`
- `filename`
- `entry_type`
- `media_source`
- `description`

Review/search JSON payloads include media-aware fields when present:

- `entry_type`
- `media_kind`
- `media_source`
- `creator`
- `published_at`
- `summary`

JSON add failure shape:

- `{"error": "..."}` with exit status `1`

## Storage Layout

```
vault_path/                       (e.g. /path/to/your/vault)
  media/
    poetry/
      20260409-a1f3.png
  topics/
    ai-reasoning.md
    investing.md
    books-to-read.md
    ...

agent-workspace/
  data/
    robin/
      robin-config.json
      robin-review-index.json

$ROBIN_HOME/                      advanced override if ROBIN_HOME is set
  config/ or data/
    robin-*.json

skill directory/
  SKILL.md
  README.md
  install.sh
  scripts/
  src/robin/
  references/robin-config.json.example
```

## Topic File Format

Entries are separated by `***`. Each entry is a frontmatter block followed by a blank line and then the body text.

```
id: 20260408-a1f3
date_added: 2026-04-08
entry_type: image
media_kind: image
media_source: media/poetry/20260408-a1f3.png
description: A photographed poem excerpt worth revisiting.
creator: Mary Oliver
published_at: 1986
summary: An excerpt about attention and observation.
tags: [poetry]

Opening lines from the photographed page.
***
id: 20260408-b7k2
date_added: 2026-04-08
entry_type: video
media_kind: video
media_source: https://www.youtube.com/watch?v=abc123
description: A talk to revisit later for its framing and examples.
creator: Speaker Name
published_at: 2025-01-01
summary: A concise summary of the talk.
tags: [talks]


```

Topic filename: lowercase topic slug with non-alphanumeric characters normalized to dashes.
Example: "AI/ML Reasoning" -> `ai-ml-reasoning.md`

Frontmatter parsing: keys are matched case-insensitively (`.lower()`). A blank line must separate frontmatter from body. Body starts at the first blank line.

Field expectations:

- `description` is required for every entry
- `creator`, `published_at`, and `summary` are required for media entries
- `media_source` is a copied vault-relative path for images and the original URL for videos

## Review Index Schema

```json
{
  "items": {
    "20260408-a1f3": {
      "id": "20260408-a1f3",
      "topic": "ai-reasoning",
      "date": "2026-04-08",
      "rating": null,
      "last_surfaced": "2026-04-08T10:00:00+00:00",
      "times_surfaced": 0
    }
  }
}
```

Item identity lives in markdown frontmatter via `id`. The review index is derived state keyed by that `id`. Review settings such as `min_items_before_review` and `review_cooldown_days` live only in `robin-config.json`, which is stored under `data/robin/` in the agent workspace by default.

## Review Cron

Create review scheduling using your host's scheduler. Robin itself only needs the host to invoke the review command periodically.

Hermes example for daily review at noon on weekdays:

```
hermes cron create \
  --name "robin:review" \
  --prompt "Run Robin review mode. Load robin-review-index.json. If items.count >= min_items_before_review, pick the best candidate (unrated first, then lowest rating, then least recently surfaced, skip if surfaced within cooldown days). Surface the item and wait for a rating (1–5). Update the index with the new rating, last_surfaced, and incremented times_surfaced." \
  --schedule "0 12 * * 1-5" \
  --skills robin \
  --deliver origin
```

## Configuration (robin-config.json)

```json
{
  "vault_path": "/path/to/your/vault",
  "topics_dir": "topics",
  "media_dir": "media",
  "min_items_before_review": 30,
  "review_cooldown_days": 60,
  "preferred_rating_scale": "1-5",
  "file_naming": "kebab"
}
```

## Design Decisions

- Config lives outside skill folder — updates to the skill do not overwrite user preferences
- Review index is separate from topic files — keeps topic files clean and human-editable
- Images are copied into the vault, but videos are only stored by URL reference
- Rating always overwrites — newer rating wins, tracked in index only
- Items identified by a stable frontmatter `id` — survives reindexing and same-day duplicates
- Index can be rebuilt — `reindex.py` scans topic files and reconstructs the index from scratch
- Agent-agnostic — works with any agent that implements a skills interface

## Pitfalls

- Don't use `---` as entry separator — it's already used to close frontmatter. Use `***`.
- Uploaded or local video files are rejected — only video URLs are allowed.
- Case-insensitive frontmatter — parse with `.lower()` on keys to handle any case variation.
- Blank line required after frontmatter — the parser stops at the first blank line. Don't put body content on the same line as the last frontmatter field.
- Keep `id` stable when manually editing entries — changing it creates a new review item.
