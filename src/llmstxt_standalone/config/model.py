"""Configuration model and derived helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
