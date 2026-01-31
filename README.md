# llmstxt-standalone

[![codecov](https://codecov.io/gh/shaanmajid/llmstxt-standalone/graph/badge.svg)](https://codecov.io/gh/shaanmajid/llmstxt-standalone)

Generate `/llms.txt` and `/llms-full.txt` from built HTML documentation, following the [llms.txt spec](https://llmstxt.org/).

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

# Show help
llmstxt-standalone -h
```

### CLI Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | `mkdocs.yml` | Path to MkDocs config file |
| `--site-dir` | `-s` | `site` | Path to built HTML directory |
| `--output-dir` | `-o` | same as site-dir | Where to write output files |
| `--verbose` | `-v` | | Show detailed progress |
| `--version` | `-V` | | Show version |
| `--help` | `-h` | | Show help |

## Configuration

Reads configuration from your `mkdocs.yml`. Two modes:

### 1. Explicit llmstxt config

```yaml
plugins:
  - llmstxt:
      markdown_description: |
        Extra context for LLMs...
      sections:
        Getting Started:
          - index.md
          - install.md
```

### 2. Nav fallback

If no `llmstxt` plugin config exists, sections are derived from `nav` automatically.

## How It Works

1. Reads `mkdocs.yml` for site metadata and section structure
1. Parses built HTML files with BeautifulSoup
1. Converts to Markdown with markdownify
1. Writes `llms.txt` (index with links) and `llms-full.txt` (full content)

## License

MIT
