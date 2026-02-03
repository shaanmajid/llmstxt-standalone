# llmstxt-standalone

[![CI](https://github.com/shaanmajid/llmstxt-standalone/actions/workflows/ci.yml/badge.svg)](https://github.com/shaanmajid/llmstxt-standalone/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/llmstxt-standalone)](https://pypi.org/project/llmstxt-standalone/)
[![Python](https://img.shields.io/pypi/pyversions/llmstxt-standalone)](https://pypi.org/project/llmstxt-standalone/)
[![License](https://img.shields.io/pypi/l/llmstxt-standalone)](https://github.com/shaanmajid/llmstxt-standalone/blob/main/LICENSE)
[![codecov](https://codecov.io/gh/shaanmajid/llmstxt-standalone/graph/badge.svg)](https://codecov.io/gh/shaanmajid/llmstxt-standalone)
[![prek](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json)](https://github.com/j178/prek)

Generate `/llms.txt`, `/llms-full.txt`, and per-page markdown files from built HTML documentation, following the [llms.txt spec](https://llmstxt.org/).

This tool works on pre-built HTML, making it useful for environments that cannot run MkDocs plugins (e.g., [Zensical](https://zensical.com/)) or when you want llms.txt generation as a separate build step. For standard MkDocs workflows, see [mkdocs-llmstxt](https://github.com/pawamoy/mkdocs-llmstxt).

## Installation

Requires Python 3.10+.

```bash
# Run without installing
uvx llmstxt-standalone

# Install as a CLI tool
uv tool install llmstxt-standalone  # or: pipx install

# Add to a project
uv add llmstxt-standalone  # or: pip install
```

## Usage

### build

Generate llms.txt from a built MkDocs site:

```bash
# Run from project root (expects mkdocs.yml and site/)
llmstxt-standalone build

# Explicit paths
llmstxt-standalone build --config mkdocs.yml --site-dir ./build --output-dir ./dist

# Preview without writing files
llmstxt-standalone build --dry-run

# Suppress output
llmstxt-standalone build --quiet

# Show detailed progress
llmstxt-standalone build --verbose
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--config` | `-c` | `mkdocs.yml` | Path to MkDocs config file |
| `--site-dir` | `-s` | `site` | Path to built HTML directory |
| `--output-dir` | `-o` | same as site-dir | Where to write output files |
| `--dry-run` | `-n` | | Preview without writing |
| `--quiet` | `-q` | | Suppress output |
| `--verbose` | `-v` | | Show detailed progress |

### init

Add llmstxt plugin configuration to an existing mkdocs.yml:

```bash
llmstxt-standalone init

# Specify config path
llmstxt-standalone init --config path/to/mkdocs.yml

# Overwrite existing llmstxt config
llmstxt-standalone init --force

# Show detailed progress
llmstxt-standalone init --verbose
```

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Path to mkdocs.yml (default: mkdocs.yml) |
| `--force` | `-f` | Overwrite existing llmstxt section |
| `--quiet` | `-q` | Suppress output |
| `--verbose` | `-v` | Show detailed progress |

### validate

Check that a config file is valid:

```bash
$ llmstxt-standalone validate
Config valid: mkdocs.yml
  Site: My Project
  Sections: 3
  Pages: 12

# Exit code only (for scripts)
llmstxt-standalone validate --quiet

# Show section details
llmstxt-standalone validate --verbose
```

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Path to mkdocs.yml (default: mkdocs.yml) |
| `--quiet` | `-q` | Suppress output |
| `--verbose` | `-v` | Show detailed config information |

### Global options

```bash
llmstxt-standalone --version  # Show version
llmstxt-standalone --help     # Show available commands
```

## Output

The `build` command generates three outputs:

1. `llms.txt` — an index file with markdown links to all pages
1. `llms-full.txt` — concatenated content of all pages
1. Per-page `.md` files alongside the HTML

The per-page markdown files make the URLs in `llms.txt` resolve to actual content. If your site is at `https://docs.example.com/`, the URL `https://docs.example.com/install/index.md` returns markdown instead of HTML.

## Configuration

The tool reads your `mkdocs.yml` for site metadata. You can configure llmstxt output explicitly or let it derive structure from your nav.

### Explicit configuration

```yaml
plugins:
  - llmstxt:
      markdown_description: |
        Extra context for LLMs about your project.
      full_output: llms-full.txt
      content_selector: article.md-content__inner
      sections:
        Getting Started:
          - index.md
          - install.md
        Usage:
          - guide/basics.md
          - guide/advanced.md
```

| Option | Default | Description |
|--------|---------|-------------|
| `markdown_description` | `""` | Additional context for LLMs, appears after site description |
| `full_output` | `llms-full.txt` | Filename for concatenated content |
| `content_selector` | auto-detect | CSS selector for main content |
| `sections` | derived from nav | Section names mapped to page lists |

### Automatic fallback

Without an explicit `llmstxt` plugin config, sections derive from your `nav` structure. Top-level pages go into a "Pages" section; nested nav items become sections named by their keys.

### MkDocs settings

The tool respects `use_directory_urls` from your mkdocs.yml. When enabled (the default), `install.md` maps to `install/index.md`; when disabled, it maps to `install.md`.

### Content extraction

If `content_selector` is not set, the tool tries these selectors in order:

1. `.md-content__inner` (Material for MkDocs)
1. `[role="main"]` (default MkDocs theme)
1. `article`
1. `main`
1. The entire document

### Title resolution

Page titles resolve in this order:

1. The title from your `nav` structure
1. The HTML `<title>` tag (with site name suffix stripped)
1. The first `<h1>` tag
1. A title derived from the filename

## Programmatic use

```python
from pathlib import Path
from llmstxt_standalone.config import load_config
from llmstxt_standalone.generate import generate_llms_txt

config = load_config(Path("mkdocs.yml"))
result = generate_llms_txt(config, site_dir=Path("site"))

print(result.llms_txt)       # Index content
print(result.llms_full_txt)  # Full content
print(result.markdown_files) # List of written .md paths
```

## Compatibility

- Produces output identical to mkdocs-llmstxt when configured the same way
- Handles Unicode, international characters, and special characters
- Works with Material for MkDocs, ReadTheDocs, and the default MkDocs theme
- Parses configs containing Python YAML tags like `!python/object/apply`

## License

MIT
