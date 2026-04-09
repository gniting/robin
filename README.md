# Robin  ·  [skills.sh](https://github.com/vercel-labs/skills)

A digital commonplace book for AI agents — collect, curate, and periodically review items from your personal digital Commonplace Book

> Dedicated to and named for [Robin Williams'](https://en.wikipedia.org/wiki/Robin_Williams) portrayal of Sean Maguire in *[Good Will Hunting](https://en.wikipedia.org/wiki/Good_Will_Hunting)* — a therapist who helped a brilliant but lost young man find his voice.

## What is a Commonplace Book?

A commonplace book[[1](https://ryanholiday.net/how-and-why-to-keep-a-commonplace-book/)][[2](https://en.wikipedia.org/wiki/Commonplace_book)] is a personal collection of ideas, phrases, and passages worth keeping. Traditionally, it is a notebook where one gathers quotations, observations, arguments, anecdotes, and striking turns of phrase from what they read or hear, then organizes them so those pieces can be revisited and used later. 
One of its most practical benefits is that it sharpens vocabulary: by repeatedly noticing, recording, and returning to precise language, a reader begins to absorb better words, clearer sentence patterns, and more nuanced ways of expressing ideas. That expanded command of language tends to improve communication, because stronger vocabulary makes it easier to speak and write with accuracy, persuasion, and confidence. 
Over time, a commonplace book becomes more than a record of reading. It turns into a tool for better thinking, better communication, and, by extension, better work, relationships, and decision-making.


## Features

You feed Robin things you want to remember — quotes, articles, links, thoughts, images, and video links — and it files them into topic-organized markdown files. Robin also runs a spaced-repetition review engine that surfaces items on a schedule so you reinforce learning over time.

- Filing — Send Robin any content and it determines the right topic, files it away, and confirms
- Media-aware filing — Local images are copied into the vault, video URLs are stored by reference, and uploaded/local video files are rejected
- Topic management — Creates new topics on demand, suggests topic names, resolves conflicts
- Spaced repetition review — Surfaces items on a configurable schedule so you reinforce learning
- Rating — Rate surfaced items 1–5; Robin tracks what you care about most over time
- Searchable vault — All entries live in plain markdown topic files; open in Obsidian, Logseq, or any editor
- Agent-agnostic — Works with any agent that implements a skills interface

## Prerequisites

- An AI agent that supports filesystem-backed skills
- Python 3.11+ (for the supporting scripts)
- A vault directory on the skill host (local filesystem)

## What Robin Stores

Robin stores plain markdown entries in topic files plus a separate review index.

- Text entries: stored directly in topic markdown files
- Image entries: the image file is copied into `vault_path/media/` and the markdown entry stores the copied relative path
- Video entries: only video URLs are stored; Robin does not download or copy video files
- Review state: ratings and surfacing metadata live in Robin's runtime data directory

Robin does not do the semantic analysis itself. The host AI agent must decide topic placement and, for media entries, must also provide the required metadata Robin stores.

Normal Robin usage should only write to your vault and review index. It should not modify the Robin skill code or docs unless you explicitly ask your agent to update Robin itself.

## Quick Start

### 1. Install the skill

Make the Robin directory available to your agent host using that host's normal skill-loading mechanism. Robin itself does not require a Hermes-style install path.

### 2. First-run setup

Run the install script:
```
bash /path/to/robin/install.sh
```

Optional:
```
bash /path/to/robin/install.sh --robin-home /path/to/robin-runtime
```

By default, Robin stores:

- config in `${XDG_CONFIG_HOME:-~/.config}/robin/robin-config.json`
- review state in `${XDG_DATA_HOME:-~/.local/share}/robin/robin-review-index.json`

If `ROBIN_HOME` is set, Robin instead uses:

- `$ROBIN_HOME/config/robin-config.json`
- `$ROBIN_HOME/data/robin-review-index.json`

If neither `ROBIN_HOME` nor XDG variables are set, Robin can still fall back to `HERMES_HOME/data` for compatibility with older Hermes-style setups.

The install script creates `robin-config.json` from the example template. Alternatively, create it manually:
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

### 3. Create your vault directory

```bash
mkdir -p /path/to/your/vault/topics /path/to/your/vault/media
```

### 4. Start filing

Just send Robin things you want to collect:

```
Robin, this quote from Paul Graham:
"The most important thing is to decide what you are optimizing for."
```

Robin will file it under an appropriate topic and confirm.

For media items, the agent must also provide structured context:

- `description` for all entries
- `creator`, `published_at`, and `summary` for image and video entries

If those required fields are missing for a media item, Robin rejects the entry instead of storing an incomplete record.

### 5. Set up review cron

Set up periodic review using whatever scheduling mechanism your host supports. Robin itself only provides the review command; it does not require any specific cron system.

Hermes example:

```bash
hermes cron create \
  --name "robin:review" \
  --prompt "Run Robin's review mode..." \
  --schedule "0 12 * * 1-5" \
  --skills robin \
  --deliver origin
```

## Vault Structure

```
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
    ...
```

Topic filename format: lowercase topic slug with non-alphanumeric characters normalized to dashes (e.g. "Song Lyrics" -> `song-lyrics.md`, "AI/ML" -> `ai-ml.md`).

## Topic File Format

Entries are separated by `***`. Each entry has a frontmatter block (key:value lines) followed by a blank line, then the body text. New entries carry a compact stable `id` so review state survives reindexing and manual file edits, plus contextual fields the agent must supply when filing media.

```
id: 20260408-a1f3
date_added: 2026-04-08
source: https://example.com/article
description: A short excerpt from a Paul Graham essay about optimizing for what matters. Useful as a general reminder when making tradeoff decisions.
tags: [ai, reasoning]

**Source:** [article title](https://example.com/article)

Notable excerpt or the thing you sent.

**Robin note:** Brief curation note
***
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

Frontmatter keys are matched case-insensitively. A blank line must separate frontmatter from body.

Field meaning:

- `entry_type`: `text`, `image`, or `video`
- `media_kind`: same as `entry_type` for media entries; omitted for text entries
- `media_source`: copied relative path for images, external URL for videos, omitted for text entries
- `description`: required contextual explanation for all entries
- `creator`, `published_at`, `summary`: required for media entries, omitted for text entries

## Media Rules

Robin accepts media with these rules:

- Local image files: accepted and copied into the vault media directory
- Remote image URLs: not supported directly by Robin's CLI; the host agent should download or otherwise resolve them before filing
- Video URLs: accepted and stored by reference
- Uploaded or local video files: rejected
- If a media item is rejected, Robin stores nothing and returns an error for the host agent to pass back to the user

Robin will not store an image or video entry unless the host agent provides:

- `description`
- `creator`
- `published_at`
- `summary`

## Commands

Skill actions:
`robin review` — Manually trigger a review cycle
`robin reindex` — Rebuild review index from topic files
`robin search <query>` — Search all topics for matching entries
`robin topics` — List all existing topics
`robin add` — File something new (or just send content directly)
`robin setup` — First-run config wizard

Installed CLI entry points:
`robin-add`
`robin-review`
`robin-reindex`
`robin-search`
`robin-topics`

Repo-local script entry points:
`python3 scripts/add_entry.py`
`python3 scripts/review.py`
`python3 scripts/reindex.py`
`python3 scripts/search.py`
`python3 scripts/topics.py`

Examples:

```bash
robin-search "clear thinking"
robin-review --rate 20260408-a1f3 5
robin-topics --json
robin-add --topic "reasoning" --content "The most important thing is to decide what you are optimizing for." --description "A short Paul Graham line about choosing the objective before optimizing. Useful when reviewing tradeoff-heavy decisions."
robin-add --entry-type image --topic "poetry" --media-path ~/Downloads/poem.png --description "A photographed poem excerpt worth revisiting." --creator "Mary Oliver" --published-at "1986" --summary "An excerpt about attention and observation."
robin-add --entry-type video --topic "talks" --media-url "https://www.youtube.com/watch?v=abc123" --description "A talk to revisit for its framing and examples." --creator "Speaker Name" --published-at "2025-01-01" --summary "A concise summary of the talk."
```

## Implementation Layout

Robin is structured as a small Python package plus thin CLI wrappers:

```text
scripts/     CLI wrappers for add/review/reindex/search/topics
src/robin/   shared config, parser, serializer, index, review, and search logic
tests/       parser and workflow tests
```

## Review System

Robin maintains a review index keyed by entry `id`. By default it lives at `${XDG_DATA_HOME:-~/.local/share}/robin/robin-review-index.json`, or under `$ROBIN_HOME/data/` when `ROBIN_HOME` is set. It tracks only review state:

- rating — your 1–5 rating (overwritten on each new rating)
- last_surfaced — when Robin last showed you this item
- times_surfaced — how many times Robin has surfaced it

When review fires:

1. Robin picks the best candidate (unrated first, then lowest rating, then least recently surfaced)
2. Skips items surfaced within the last `review_cooldown_days`
3. Surfaces the item with context
4. You rate it 1–5
5. Robin updates the index

Robin only triggers a review when you have at least `min_items_before_review` items in your vault.

When resurfacing an entry, Robin shows the saved content, contextual `description`, and any media metadata and media reference.

Ratings are applied by stable entry id, for example:

```bash
robin-review --rate 20260408-a1f3 5
```

All CLI helpers support `--json` for agent-friendly integration.

## Host Examples

Robin is host-neutral. The exact install and scheduling commands depend on your agent platform.

Hermes example:

```bash
hermes skills install /path/to/robin
```

Other hosts such as OpenClaw, Claude Code, or Codex should load the same directory using their own local-skill mechanism.

Error behavior:

- missing required fields produce an error and the entry is not stored
- invalid image paths produce an error and the entry is not stored
- local or uploaded video files produce an error and the entry is not stored
- `--json` mode returns machine-readable errors like `{"error": "..."}` for failed add operations

## Compatibility Notes

- New entries include a compact frontmatter `id`.
- New entries should also include a 2-3 sentence `description` generated by the host agent.
- Media entries must also include `creator`, `published_at`, and `summary`.
- Local images are copied into the vault media directory and resurfaced from there.
- Video URLs are stored by reference and resurfaced as links.
- Uploaded or local video files are rejected.
- Older markdown entries without `id` still work.
- Reindex derives stable fallback ids for legacy entries that do not yet carry one.
- Topic files remain plain markdown and are intended to stay usable in tools like Obsidian and Logseq.

## Install Behavior

`install.sh` checks system requirements and fails gracefully if they are not met. It reports what is missing, but it does not install any dependencies for you.

It also supports `--robin-home` if you want Robin's config and review index stored under a dedicated runtime root instead of XDG defaults.

## Configuration Reference

| Key | Default | Description |
|---|---|---|
| `vault_path` | required | Path to your vault root |
| `topics_dir` | `"topics"` | Subdirectory for topic files |
| `media_dir` | `"media"` | Subdirectory for copied image assets |
| `min_items_before_review` | `30` | Min items before review triggers |
| `review_cooldown_days` | `60` | Days before an item can be surfaced again |
| `preferred_rating_scale` | `"1-5"` | Rating scale (currently fixed to 1-5) |
| `file_naming` | `"kebab"` | Filename convention (kebab-case) |

## Syncing to Other Devices

Robin writes to a local vault path. To access it from other devices:

- Rsync over SSH — periodically sync the vault to your other devices
- SMB share — mount the vault directory on your MacBook
- Git — commit and push the vault to a private Git repo, pull on other devices

Syncing is not built into Robin; choose the method that fits your setup.

## License

MIT — see [LICENSE](LICENSE)
