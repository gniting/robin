# Robin Guide

This guide covers the detailed behavior and reference material for Robin.

## Runtime Paths

Robin stores runtime state outside the skill directory.

- If `ROBIN_HOME` is set:
  - config: `$ROBIN_HOME/config/robin-config.json`
  - review index: `$ROBIN_HOME/data/robin-review-index.json`
- Otherwise, Robin uses XDG defaults:
  - config: `${XDG_CONFIG_HOME:-~/.config}/robin/robin-config.json`
  - review index: `${XDG_DATA_HOME:-~/.local/share}/robin/robin-review-index.json`
- Compatibility fallback:
  - if neither `ROBIN_HOME` nor the relevant XDG variable is set, Robin can use `HERMES_HOME/data`

## Install Behavior

Run:

```bash
bash /path/to/robin/install.sh
```

Optional:

```bash
bash /path/to/robin/install.sh --robin-home /path/to/robin-runtime
```

`install.sh`:

- checks system requirements
- creates Robin-owned config/data directories
- initializes `robin-config.json`
- initializes `robin-review-index.json`
- creates the configured vault `topics/` and `media/` directories when `vault_path` is available

It does not install dependencies.

## Vault Structure

```text
vault_path/
  media/
    poetry/
      20260409-a1f3.png
  topics/
    reasoning.md
    lyrics.md
    poetry.md
    idioms.md
    quotes.md
```

Topic filenames use lowercase slugs with non-alphanumeric characters normalized to dashes.

Examples:

- `Song Lyrics` -> `song-lyrics.md`
- `AI/ML` -> `ai-ml.md`

## Topic File Format

Entries are separated by `***`. Each entry has a frontmatter block, then a blank line, then the body text.

Text example:

```text
id: 20260408-a1f3
date_added: 2026-04-08
source: https://example.com/article
description: A short excerpt from a Paul Graham essay about optimizing for what matters. Useful as a general reminder when making tradeoff decisions.
tags: [ai, reasoning]

**Source:** [article title](https://example.com/article)

Notable excerpt or the thing you sent.

**Robin note:** Brief curation note
```

Image example:

```text
id: 20260408-b7k2
date_added: 2026-04-08
entry_type: image
media_kind: image
media_source: media/poetry/20260408-b7k2.png
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
- `source`: original article/source URL for text or optional metadata for media
- `description`: required contextual explanation for every entry
- `creator`, `published_at`, `summary`: required for media entries
- `tags`: optional tag list

Frontmatter keys are matched case-insensitively. A blank line must separate frontmatter from body.

## Media Rules

Robin accepts media with these rules:

- Local image files: accepted and copied into the vault media directory
- Remote image URLs: not supported directly by Robin's CLI; the host agent should download or resolve them before filing
- Video URLs: accepted and stored by reference
- Uploaded or local video files: rejected

Robin will not store an image or video entry unless the host agent provides:

- `description`
- `creator`
- `published_at`
- `summary`

If a media item is rejected, Robin stores nothing and returns an error.

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

Examples:

```bash
robin-search "clear thinking"
robin-review --rate 20260408-a1f3 5
robin-topics --json
robin-add --topic "reasoning" --content "The most important thing is to decide what you are optimizing for." --description "A short Paul Graham line about choosing the objective before optimizing. Useful when reviewing tradeoff-heavy decisions."
robin-add --entry-type image --topic "poetry" --media-path ~/Downloads/poem.png --description "A photographed poem excerpt worth revisiting." --creator "Mary Oliver" --published-at "1986" --summary "An excerpt about attention and observation."
robin-add --entry-type video --topic "talks" --media-url "https://www.youtube.com/watch?v=abc123" --description "A talk to revisit for its framing and examples." --creator "Speaker Name" --published-at "2025-01-01" --summary "A concise summary of the talk."
```

All CLI helpers support `--json`.

## Review System

Robin maintains a review index keyed by entry `id`. It stores only review state:

- `rating`
- `last_surfaced`
- `times_surfaced`

Review behavior:

1. Robin waits until you have at least `min_items_before_review` items.
2. It prefers unrated items first.
3. Then it prefers lower-rated items.
4. Then it prefers items least recently surfaced.
5. It skips items surfaced within `review_cooldown_days`.
6. Rating overwrites the previous rating and increments `times_surfaced`.

Example index shape:

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

## Configuration Reference

Example config:

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

| Key | Default | Description |
|---|---|---|
| `vault_path` | required | Path to your vault root |
| `topics_dir` | `"topics"` | Subdirectory for topic files |
| `media_dir` | `"media"` | Subdirectory for copied image assets |
| `min_items_before_review` | `30` | Min items before review triggers |
| `review_cooldown_days` | `60` | Days before an item can be surfaced again |
| `preferred_rating_scale` | `"1-5"` | Rating scale |
| `file_naming` | `"kebab"` | Filename convention |

## Host Examples

Robin is host-neutral. Use your host's normal local-skill mechanism.

Hermes example install:

```bash
hermes skills install /path/to/robin
```

Hermes example review scheduling:

```bash
hermes cron create \
  --name "robin:review" \
  --prompt "Run Robin's review mode..." \
  --schedule "0 12 * * 1-5" \
  --skills robin \
  --deliver origin
```

Other hosts such as OpenClaw, Claude Code, or Codex should load the same directory using their own local-skill mechanism.

## Compatibility Notes

- New entries include a compact frontmatter `id`
- New entries should include a 2-3 sentence `description` generated by the host agent
- Older markdown entries without `id` still work
- Reindex derives stable fallback ids for legacy entries
- Topic files remain plain markdown and are intended to stay usable in tools like Obsidian and Logseq

## Error Behavior

- Missing required fields produce an error and the entry is not stored
- Invalid image paths produce an error and the entry is not stored
- Local or uploaded video files produce an error and the entry is not stored
- `--json` mode returns machine-readable errors like `{"error": "..."}` for failed add operations

## Syncing to Other Devices

Robin writes to a local vault path. To access it from other devices:

- Rsync over SSH
- SMB share
- Git

Syncing is not built into Robin.
