"""Configuration loading from mkdocs.yml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llmstxt_standalone.config.derive import nav_to_sections
from llmstxt_standalone.config.model import Config
from llmstxt_standalone.config.plugin import get_llmstxt_config

DEFAULT_SITE_NAME = "Documentation"
DEFAULT_FULL_OUTPUT = "llms-full.txt"


class _PermissiveLoader(yaml.SafeLoader):
    """SafeLoader that ignores unknown Python tags.

    MkDocs extensions like pymdownx.slugs use Python-specific YAML tags
    like !python/object/apply which SafeLoader rejects. This loader
    treats them as raw strings to allow parsing the rest of the config.
    """


def _ignore_unknown(loader: yaml.Loader, tag_suffix: str, node: yaml.Node) -> str:
    """Return the raw tag as a placeholder string."""
    return f"<{node.tag}>"


# Register handler for all Python tags (both full and shorthand forms)
_PermissiveLoader.add_multi_constructor("tag:yaml.org,2002:python/", _ignore_unknown)
_PermissiveLoader.add_multi_constructor("!python/", _ignore_unknown)


def load_config(config_path: Path) -> Config:
    """Load and resolve configuration from mkdocs.yml.

    Args:
        config_path: Path to mkdocs.yml file.

    Returns:
        Resolved Config object.

    Raises:
        FileNotFoundError: If config file doesn't exist.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        raw = yaml.load(f, Loader=_PermissiveLoader)

    if not isinstance(raw, dict):
        raise ValueError(f"Config file must be a mapping: {config_path}")

    return _config_from_mkdocs(raw)


def _config_from_mkdocs(raw: dict[str, Any]) -> Config:
    """Build a Config from a parsed mkdocs.yml mapping."""
    site_name = raw.get("site_name", DEFAULT_SITE_NAME)
    site_description = raw.get("site_description", "")
    site_url = raw.get("site_url", "").rstrip("/")
    nav = raw.get("nav", [])
    # MkDocs defaults use_directory_urls to true
    use_directory_urls = raw.get("use_directory_urls", True)

    llmstxt_config = get_llmstxt_config(raw)

    if llmstxt_config is not None:
        markdown_description = llmstxt_config.get("markdown_description", "")
        full_output = llmstxt_config.get("full_output", DEFAULT_FULL_OUTPUT)
        content_selector = llmstxt_config.get("content_selector")
        sections = llmstxt_config.get("sections", {})
        if not isinstance(sections, dict):
            raise ValueError(
                f"llmstxt 'sections' must be a mapping, got {type(sections).__name__}"
            )
        for section_name, pages in sections.items():
            if not isinstance(section_name, str):
                raise ValueError(
                    "llmstxt 'sections' keys must be strings, "
                    f"got {type(section_name).__name__}"
                )
            if not isinstance(pages, list):
                raise ValueError(
                    f"llmstxt 'sections.{section_name}' must be a list of strings, "
                    f"got {type(pages).__name__}"
                )
            for page in pages:
                if not isinstance(page, str):
                    raise ValueError(
                        f"llmstxt 'sections.{section_name}' entries must be strings, "
                        f"got {type(page).__name__}"
                    )
    else:
        markdown_description = ""
        full_output = DEFAULT_FULL_OUTPUT
        content_selector = None
        sections = nav_to_sections(nav)

    return Config(
        site_name=site_name,
        site_description=site_description,
        site_url=site_url,
        markdown_description=markdown_description,
        full_output=full_output,
        content_selector=content_selector,
        sections=sections,
        nav=nav,
        use_directory_urls=use_directory_urls,
    )
