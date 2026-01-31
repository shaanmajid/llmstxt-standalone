"""Helpers for deriving config sections from nav."""

from __future__ import annotations

from typing import Any


def nav_to_sections(nav: list[Any]) -> dict[str, list[str]]:
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
    pages: list[str] = []
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
