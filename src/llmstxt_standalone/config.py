"""Configuration loading and resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Config:
    """Resolved configuration for llmstxt generation."""

    site_name: str
    site_description: str
    site_url: str
    markdown_description: str
    full_output: str
    content_selector: str | None
    sections: dict[str, list[str]]
    nav: list[Any]
    use_directory_urls: bool = True

    def get_page_title(self, md_path: str) -> str:
        """Find the title for a page from the nav structure."""
        title = self._search_nav(self.nav, md_path)
        if title:
            return title
        # Fallback: derive from filename
        return md_path.replace(".md", "").replace("-", " ").replace("/", " - ").title()

    def _search_nav(self, items: list[Any], md_path: str) -> str | None:
        """Recursively search nav for a page title."""
        for item in items:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, str) and value == md_path:
                        return key
                    if isinstance(value, list):
                        result = self._search_nav(value, md_path)
                        if result:
                            return result
        return None


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
        raw = yaml.load(f, Loader=yaml.SafeLoader)

    site_name = raw.get("site_name", "Documentation")
    site_description = raw.get("site_description", "")
    site_url = raw.get("site_url", "").rstrip("/")
    nav = raw.get("nav", [])
    # MkDocs defaults use_directory_urls to true
    use_directory_urls = raw.get("use_directory_urls", True)

    # Extract llmstxt plugin config if present
    llmstxt_config = _get_llmstxt_config(raw)

    if llmstxt_config is not None:
        markdown_description = llmstxt_config.get("markdown_description", "")
        full_output = llmstxt_config.get("full_output", "llms-full.txt")
        content_selector = llmstxt_config.get("content_selector")
        sections = llmstxt_config.get("sections", {})
    else:
        # Fallback: derive sections from nav
        markdown_description = ""
        full_output = "llms-full.txt"
        content_selector = None
        sections = _nav_to_sections(nav)

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


def _get_llmstxt_config(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Extract llmstxt plugin config from mkdocs.yml plugins.

    MkDocs supports two plugin config styles:

    List form:
        plugins:
          - llmstxt:
              sections: ...

    Mapping form:
        plugins:
          llmstxt:
            sections: ...
    """
    plugins = raw.get("plugins")
    if plugins is None:
        return None

    # Mapping form: plugins is a dict with plugin names as keys
    if isinstance(plugins, dict):
        if "llmstxt" in plugins:
            config = plugins["llmstxt"]
            # Plugin with no options is represented as empty dict or None
            return config if isinstance(config, dict) else {}
        return None

    # List form: plugins is a list of strings or dicts
    for plugin in plugins:
        if isinstance(plugin, dict) and "llmstxt" in plugin:
            return plugin["llmstxt"]
        if plugin == "llmstxt":
            return {}
    return None


def _nav_to_sections(nav: list[Any]) -> dict[str, list[str]]:
    """Convert nav structure to sections dict."""
    sections: dict[str, list[str]] = {}

    for item in nav:
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, str):
                    # Top-level page, add to "Pages" section
                    sections.setdefault("Pages", []).append(value)
                elif isinstance(value, list):
                    # Section with children
                    pages = _extract_pages(value)
                    if pages:
                        sections[key] = pages

    return sections


def _extract_pages(items: list[Any]) -> list[str]:
    """Extract page paths from nav items."""
    pages = []
    for item in items:
        if isinstance(item, str):
            pages.append(item)
        elif isinstance(item, dict):
            for value in item.values():
                if isinstance(value, str):
                    pages.append(value)
                elif isinstance(value, list):
                    pages.extend(_extract_pages(value))
    return pages
