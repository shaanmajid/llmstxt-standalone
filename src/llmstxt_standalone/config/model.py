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

    def get_nav_title(self, md_path: str) -> str | None:
        """Find the title for a page from the nav structure only.

        Returns None if the page is not found in nav or has no explicit title.
        """
        return self._search_nav(self.nav, md_path, section_title=None)

    def get_filename_title(self, md_path: str) -> str:
        """Derive title from filename path."""
        return md_path.replace(".md", "").replace("-", " ").replace("/", " - ").title()

    def get_page_title(self, md_path: str) -> str:
        """Find the title for a page from the nav structure with fallback."""
        return self.get_nav_title(md_path) or self.get_filename_title(md_path)

    def _search_nav(
        self, items: list[Any], md_path: str, section_title: str | None
    ) -> str | None:
        """Recursively search nav for a page title.

        Args:
            items: Nav items to search (list of dicts or strings).
            md_path: Markdown file path to find.
            section_title: Title of the current section for bare string inheritance.
        """
        for item in items:
            # Bare string in a section list inherits section title
            if isinstance(item, str) and item == md_path:
                return section_title
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, str) and value == md_path:
                        return key
                    if isinstance(value, list):
                        result = self._search_nav(value, md_path, section_title=key)
                        if result:
                            return result
        return None
