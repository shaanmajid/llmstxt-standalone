# llmstxt-standalone

[![codecov](https://codecov.io/gh/shaanmajid/llmstxt-standalone/graph/badge.svg)](https://codecov.io/gh/shaanmajid/llmstxt-standalone)

Generate `/llms.txt`, `/llms-full.txt`, and per-page markdown files from built HTML documentation, following the [llms.txt spec](https://llmstxt.org/).

> **When to use this:** This tool works on pre-built HTML, making it useful for environments that can't run MkDocs plugins (e.g., [Zensical](https://zensical.com/)) or when you want llms.txt generation as a separate build step. If you're using standard MkDocs, also consider [mkdocs-llmstxt](https://github.com/pawamoy/mkdocs-llmstxt).

## Installation

```bash
uv tool install llmstxt-standalone
# or
pipx install llmstxt-standalone
```

## Usage

```bash
# Run from project root (looks for mkdocs.yml + site/)
llmstxt-standalone

# Explicit paths
llmstxt-standalone --config mkdocs.yml --site-dir ./build --output-dir ./dist

# Preview without writing files
llmstxt-standalone --dry-run

# Suppress output (useful in CI)
llmstxt-standalone --quiet

# Show detailed progress
llmstxt-standalone --verbose

# Show help
llmstxt-standalone -h
```

### CLI Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | `mkdocs.yml` | Path to MkDocs config file |
| `--site-dir` | `-s` | `site` | Path to built HTML directory |
| `--output-dir` | `-o` | same as site-dir | Where to write llms.txt files |
| `--dry-run` | `-n` | | Preview what would be generated without writing |
| `--quiet` | `-q` | | Suppress output (exit code only) |
| `--verbose` | `-v` | | Show detailed progress |
| `--version` | `-V` | | Show version |
| `--help` | `-h` | | Show help |

## What It Generates

1. **`llms.txt`** — Index file with links to all pages (markdown URLs)
1. **`llms-full.txt`** — Full concatenated content of all pages
1. **Per-page `.md` files** — Individual markdown files alongside HTML

The per-page markdown files make the URLs in `llms.txt` actually work. For example, if your site is at `https://docs.example.com/`, the URL `https://docs.example.com/install/index.md` will return clean markdown instead of HTML.

## Configuration

Reads configuration from your `mkdocs.yml`. Two modes:

### 1. Explicit llmstxt config

```yaml
plugins:
  - llmstxt:
      markdown_description: |
        Extra context for LLMs about your project.
        This appears after the site description.
      full_output: llms-full.txt
      content_selector: article.md-content__inner  # CSS selector for main content
      sections:
        Getting Started:
          - index.md
          - install.md
        Usage:
          - guide/basics.md
          - guide/advanced.md
```

### 2. Nav fallback

If no `llmstxt` plugin config exists, sections are derived from `nav` automatically.

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `markdown_description` | `""` | Additional description text for LLMs |
| `full_output` | `llms-full.txt` | Filename for the full content file |
| `content_selector` | auto-detect | CSS selector for extracting main content |
| `sections` | derived from nav | Dict of section names to page lists |

## How It Works

1. Reads `mkdocs.yml` for site metadata and section structure
1. Parses built HTML files with BeautifulSoup
1. Converts to Markdown with markdownify (preserving code blocks, links, etc.)
1. Writes `llms.txt` (index with links) and `llms-full.txt` (full content)
1. Writes individual `.md` files alongside HTML for each page

## Compatibility

- **Output parity with mkdocs-llmstxt** — Produces identical output when configured the same way
- **Unicode support** — Handles international characters, emojis, and special characters
- **MkDocs themes** — Works with Material for MkDocs, ReadTheDocs, and default themes
- **Python YAML tags** — Handles configs with `!python/object/apply` and similar tags

## License

MIT
