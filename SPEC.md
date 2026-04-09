# Robin — Digital Commonplace Book

## Name

Robin

## Description

A digital commonplace book for AI agents. Collect, curate, and periodically review items from your personal knowledge base. Inspired by the 17th–19th century tradition of collecting quotes, ideas, and observations in a personal "commonplace book."

Named for Robin Williams' portrayal of Sean Maguire in Good Will Hunting.

## Category

Personal Knowledge Management

## Core Features

1. **Filing** — Send Robin any content (quote, link, article, thought). It determines the right topic, files it away, and confirms.
2. **Topic management** — Creates new topics on demand, suggests topic names, resolves ambiguity.
3. **Spaced repetition review** — Surfaces items on a configurable schedule so you reinforce learning over time.
4. **Rating** — Rate surfaced items 1–5; Robin tracks what resonates most.
5. **Searchable vault** — All entries live in plain markdown topic files; open in Obsidian, Logseq, or any editor.
6. **Agent-agnostic** — Works with any agent that implements a skills interface (Hermes, OpenClaw, Claude Code, Codex, etc.).

## Interaction Patterns

### Filing (default)

1. User sends content (text, link, quote, note)
2. Robin scans existing topic files, picks the best match
3. If confident — file it and confirm
4. If unsure between two topics — ask the user to choose
5. If no match exists — suggest a new topic name, file it, flag for review

### Review Mode

Triggered by the review cron or `/robin review`. Only runs when `items.count >= min_items_before_review`:

1. Pick the best candidate: unrated items first, then lowest rating, then least recently surfaced
2. Skip any item surfaced within `review_cooldown_days`
3. Surface the item to the user with context
4. User rates it 1–5
5. Robin updates the review index — rating is always overwritten with the new one
6. Increment `times_surfaced`, set `last_surfaced`

### Commands

- `robin review` — Manually trigger a review cycle
- `robin reindex` — Rebuild review index from topic files (use after manual edits)
- `robin search <query>` — Find entries matching query across all topics
- `robin topics` — List all existing topics
- `robin add` — File something new (can also just send content directly)
- `robin setup` — First-run config wizard

## Storage Layout

```
vault_path/                       e.g. /opt/commonplace-book
  topics/
    ai-reasoning.md
    investing.md
    books-to-read.md
    ...

~/.hermes/data/                   (or $HERMES_HOME/data/)
  cb-config.json                   user config (create from example on first run)
  cb-review-index.json             review metadata, managed by skill

~/.hermes/skills/robin/            skill installation
  SKILL.md                         this file
  README.md                        user-facing documentation
  LICENSE                          MIT
  scripts/
    add_entry.py
    review.py
    reindex.py
    search.py
    topics.py
  references/
    cb-config.json.example         setup template, safe to overwrite on update
```

## Topic File Format

Entries are separated by `***` (NOT `---`). The `---` marker appears in two places per entry (closing frontmatter AND trailing separator), which makes naive string splitting ambiguous. `***` never appears in frontmatter or body, so splitting on it is reliable.

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

Frontmatter parsing: keys are matched case-insensitively (`.lower()`). A blank line must separate frontmatter from body.

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

Item identity lives in markdown frontmatter via `id`. The review index is derived state keyed by that id.

## Configuration Reference

| Key | Default | Description |
|---|---|---|
| `vault_path` | required | Path to your vault root |
| `topics_dir` | `"topics"` | Subdirectory for topic files |
| `min_items_before_review` | `30` | Min items before review triggers |
| `review_cooldown_days` | `60` | Days before an item can be surfaced again |
| `preferred_rating_scale` | `"1-5"` | Rating scale (currently fixed to 1-5) |
| `file_naming` | `"kebab"` | Filename convention (kebab-case) |

## Design Decisions

- **Config lives outside skill folder** — updates to the skill do not overwrite user preferences
- **Review index is separate from topic files** — keeps topic files clean and human-editable
- **Rating always overwrites** — newer rating wins, tracked in index only
- **Index key is the stable entry id** — supports duplicates without relying on file position
- **Index can be rebuilt** — `reindex.py` scans topic files and reconstructs the index from scratch
- **Agent-agnostic** — works with any agent that implements a skills interface

## Pitfalls

- **Don't use `---` as entry separator** — it's used to close frontmatter. Use `***`.
- **Case-insensitive frontmatter** — parse with `.lower()` on keys to handle any case variation.
- **Blank line required after frontmatter** — the parser stops at the first blank line. Don't put body content on the same line as the last frontmatter field.
- **Keep `id` stable** — changing it manually creates a new review item.
