# Robin  ·  [skills.sh](https://github.com/vercel-labs/skills)

A digital commonplace book for AI agents. Use Robin to save and review notes, quotes, articles, links, images, and video references in topic-organized Markdown files.

> Named for Robin Williams' portrayal of Sean Maguire in *Good Will Hunting*.

## Features

- Files saved content into plain Markdown topic files you can inspect directly
- Supports text, local images, and video URLs
- Stores review metadata separately and resurfaces saved items over time
- Works with any host that can run the bundled Python scripts

## Prerequisites

- An agent host that supports local, filesystem-backed skills
- Python 3.11+
- A local vault directory

## Quick Start

### 1. Install the skill

Make the Robin directory available to your agent host using that host's normal local-skill mechanism.

### 2. Run setup

```bash
bash /path/to/robin/install.sh
```

Optional:

```bash
bash /path/to/robin/install.sh --robin-home /path/to/robin-runtime
```

By default, Robin stores:

- config in `${XDG_CONFIG_HOME:-~/.config}/robin/robin-config.json`
- review state in `${XDG_DATA_HOME:-~/.local/share}/robin/robin-review-index.json`

If `ROBIN_HOME` is set, Robin instead uses:

- `$ROBIN_HOME/config/robin-config.json`
- `$ROBIN_HOME/data/robin-review-index.json`

### 3. Create your vault

```bash
mkdir -p /path/to/your/vault/topics /path/to/your/vault/media
```

### 4. Start filing

Example:

```text
Robin, save this quote:
"The most important thing is to decide what you are optimizing for."
```

For media items, the host agent must also provide:

- `description` for every entry
- `creator`, `published_at`, and `summary` for image and video entries

### 5. Review saved items

```bash
robin-review
robin-review --rate 20260408-a1f3 5
```

## What Robin Stores

- Topic files in your vault under `topics/`
- Copied images in your vault under `media/<topic>/`
- Review metadata in Robin's runtime data directory

Robin stores content and review state. The host agent is responsible for topic selection, contextual summaries, and media metadata extraction.

## Commands

Installed CLI entry points:

- `robin-add`
- `robin-review`
- `robin-reindex`
- `robin-search`
- `robin-topics`

Repo-local script entry points:

- `python3 scripts/add_entry.py`
- `python3 scripts/review.py`
- `python3 scripts/reindex.py`
- `python3 scripts/search.py`
- `python3 scripts/topics.py`

Examples:

```bash
robin-search "clear thinking"
robin-topics --json
robin-add --topic "reasoning" --content "The most important thing is to decide what you are optimizing for." --description "A short Paul Graham line about choosing the objective before optimizing. Useful when reviewing tradeoff-heavy decisions."
```

## More Detail

See [docs/guide.md](/home/hermes/.hermes/skills/personal/robin/docs/guide.md) for:

- topic file format and media rules
- runtime paths and configuration
- review/index behavior
- host-specific examples
- compatibility notes and error behavior

## License

MIT — see [LICENSE](/home/hermes/.hermes/skills/personal/robin/LICENSE)
