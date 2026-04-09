---
name: robin
description: A digital commonplace book — collect, curate, and periodically review items from your personal knowledge base
category: personal
---

# Robin — Personal Knowledge Curation Skill

A digital commonplace book inspired by the 17th–19th century tradition of collecting quotes, ideas, and observations. You feed Robin things you want to remember — quotes, articles, links, thoughts — and it files them into topic-organized markdown files. Robin also runs a spaced-repetition review engine that surfaces items on a schedule so you reinforce learning over time.

Named for Robin Williams' portrayal of Sean Maguire in Good Will Hunting — a reminder that the tools we build to sharpen our words are worth building well.

## Core Concepts

- **Vault path**: where your Obsidian vault lives (local on the skill host)
- **Topic files**: one markdown file per topic, entries appended chronologically, separated by `***`, each with a compact stable `id`
- **Review index**: `~/.hermes/data/cb-review-index.json` — tracks rating, last surfaced, times surfaced per item
- **Config**: `~/.hermes/data/cb-config.json` — user preferences, never overwritten on skill update
- **Config example**: shipped in `references/cb-config.json.example` for first-run setup

## Interaction Patterns

### Filing (default mode)

1. You send content (text, link, quote, note, article)
2. I scan existing topic files, pick the best match
3. If confident — file it and confirm
4. If unsure between two topics — ask you to choose
5. If no match exists — suggest a new topic name, file it, flag for review

### Review mode

Triggered by the review cron. Only runs when `items.count >= min_items_before_review`:

1. Pick the best candidate: unrated items first, then lowest rating, then least recently surfaced
2. Skip any item surfaced within `review_cooldown_days`
3. Surface the item to you with context
4. You rate it 1–5
5. I update the review index — rating is always overwritten with the new one
6. Increment `times_surfaced`, set `last_surfaced`

### Commands

- `robin review` — manually trigger a review cycle
- `robin reindex` — rebuild review index from topic files (use after manual edits)
- `robin search <query>` — find entries matching query across all topics
- `robin topics` — list all existing topics
- `robin add` — file something new (can also just send content directly)
- `robin setup` — first-run config wizard

## Storage Layout

```
vault_path/                       (e.g. /opt/commonplace-book)
  topics/
    ai-reasoning.md
    investing.md
    books-to-read.md
    ...

~/.hermes/data/
  cb-config.json                   user config (create from example on first run)
  cb-review-index.json            review metadata, managed by skill
~/.hermes/skills/robin/
  SKILL.md
  README.md
  LICENSE
  install.sh
  pyproject.toml
  scripts/
    add_entry.py
    review.py
    reindex.py
    search.py
    topics.py
  references/
    cb-config.json.example
```

## Topic File Format

Entries are separated by `***` (NOT `---`). The `---` marker appears in two places per entry (closing frontmatter AND trailing separator), making it ambiguous for naive string splitting. `***` never appears in frontmatter or body, so splitting on it is reliable.

```
id: 20260408-a1f3
date_added: 2026-04-08
source: https://example.com/article
tags: [ai, reasoning]

**Source:** [article title](https://example.com/article)

Notable excerpt or the thing you sent.

**Robin note:** Brief curation note
***
id: 20260408-b7k2
date_added: 2026-04-08
source: https://example.com/other
tags: [books]

Another entry body here.
```

Topic filename: lowercase topic name, spaces become dashes.
Example: "AI Reasoning" -> `ai-reasoning.md`

Frontmatter parsing: keys are matched case-insensitively (`.lower()`). A blank line must separate frontmatter from body. Body starts at the first blank line.

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
  },
  "config": {
    "min_items_before_review": 30,
    "review_cooldown_days": 60
  }
}
```

Item identity lives in markdown frontmatter via `id`. The review index is derived state keyed by that `id`.

## Review Cron

Create the cron separately. Example for daily review at noon on weekdays:

```
hermes cron create \
  --name "robin:review" \
  --prompt "Run Robin review mode. Load cb-review-index.json. If items.count >= min_items_before_review, pick the best candidate (unrated first, then lowest rating, then least recently surfaced, skip if surfaced within cooldown days). Surface the item and wait for a rating (1–5). Update the index with the new rating, last_surfaced, and incremented times_surfaced." \
  --schedule "0 12 * * 1-5" \
  --skills robin \
  --deliver origin
```

## Configuration (cb-config.json)

```json
{
  "vault_path": "/opt/commonplace-book",
  "topics_dir": "topics",
  "min_items_before_review": 30,
  "review_cooldown_days": 60,
  "preferred_rating_scale": "1-5",
  "file_naming": "kebab"
}
```

## Design Decisions

- Config lives outside skill folder — updates to the skill do not overwrite user preferences
- Review index is separate from topic files — keeps topic files clean and human-editable
- Rating always overwrites — newer rating wins, tracked in index only
- Items identified by a stable frontmatter `id` — survives reindexing and same-day duplicates
- Index can be rebuilt — `reindex.py` scans topic files and reconstructs the index from scratch
- Agent-agnostic — works with any agent that implements a skills interface

## Pitfalls

- Don't use `---` as entry separator — it's already used to close frontmatter. Use `***`.
- Case-insensitive frontmatter — parse with `.lower()` on keys to handle any case variation.
- Blank line required after frontmatter — the parser stops at the first blank line. Don't put body content on the same line as the last frontmatter field.
- Keep `id` stable when manually editing entries — changing it creates a new review item.
