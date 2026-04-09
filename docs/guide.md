# Robin Guide

This guide is for advanced users who want the full technical picture: storage layout, manual setup, CLI usage, review behavior, and troubleshooting.

## Recommended Storage Model

Robin's preferred default is to keep content in the user's vault and Robin state in the agent workspace.

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
      20260409-a1f3.png
  topics/
    reasoning.md
    poetry.md
    quotes.md
```

This keeps Robin's operational state inside the workspace while leaving the vault focused on user content.

## Runtime Path Resolution

Robin supports several ways to locate its config and review index.

Preferred path:

- if `ROBIN_WORKSPACE` is set:
  - config: `$ROBIN_WORKSPACE/data/robin/robin-config.json`
  - review index: `$ROBIN_WORKSPACE/data/robin/robin-review-index.json`

Automatic discovery:

- if the current working directory or one of its parents contains `data/robin/robin-config.json`, Robin uses that `data/robin/` directory

Advanced overrides:

- `ROBIN_CONFIG_FILE` for an explicit config path
- `ROBIN_INDEX_FILE` for an explicit review index path
- `ROBIN_HOME` for a separate Robin runtime root

Compatibility fallback:

- XDG config/data locations
- `HERMES_HOME/data` when neither the workspace-local nor XDG paths are available

## Install and Setup

### Recommended agent-driven setup

Ask your agent to:

- install Robin
- choose or confirm the vault path
- run Robin setup
- ensure `topics/` and `media/` exist inside the vault
- ensure `data/robin/` exists inside the agent workspace

Example prompts:

- `Install Robin from GitHub and set it up for my vault at /path/to/my/vault.`
- `Use Robin and prepare everything it needs inside my vault.`

### Manual setup

If you want to run setup yourself:

```bash
bash /path/to/robin/install.sh --vault /path/to/your/vault
```

Advanced override:

```bash
bash /path/to/robin/install.sh --vault /path/to/your/vault --robin-home /path/to/robin-runtime
```

`install.sh`:

- checks requirements
- creates config and index files
- creates `topics/` and `media/`
- writes Robin state under `data/robin/` in the workspace by default

It does not install dependencies.

## Topic Files

Robin stores content in topic-organized Markdown files under `topics/`.

Topic filenames use lowercase slugs with non-alphanumeric characters normalized to dashes.

Examples:

- `Song Lyrics` -> `song-lyrics.md`
- `AI/ML` -> `ai-ml.md`

## Entry Format

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

Robin maintains a review index keyed by entry `id`. It stores:

- `rating`
- `last_surfaced`
- `times_surfaced`

Review behavior:

1. Robin waits until there are at least `min_items_before_review` items.
2. It prefers unrated items first.
3. Then lower-rated items.
4. Then items least recently surfaced.
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
| `min_items_before_review` | `30` | Minimum items before review triggers |
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

## Troubleshooting and Compatibility

- New entries include a compact frontmatter `id`
- New entries should include a 2-3 sentence `description` generated by the host agent
- Older markdown entries without `id` still work
- Reindex derives stable fallback ids for legacy entries
- Local or uploaded video files are rejected
- Topic files remain plain Markdown and are usable in tools like Obsidian and Logseq
- If Robin cannot find its config, confirm you are running inside the workspace, or set `ROBIN_WORKSPACE`, `ROBIN_CONFIG_FILE`, or `ROBIN_INDEX_FILE`

## Error Behavior

- Missing required fields produce an error and the entry is not stored
- Invalid image paths produce an error and the entry is not stored
- Local or uploaded video files produce an error and the entry is not stored
- `--json` mode returns machine-readable errors like `{"error": "..."}` for failed add operations
