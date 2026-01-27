"""Tests for configuration loading."""

from pathlib import Path

import pytest

from llmstxt_gen.config import load_config

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_config_with_llmstxt_plugin():
    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

    assert config.site_name == "Test Site"
    assert config.site_description == "A test site"
    assert config.site_url == "https://test.com"
    assert "Custom description" in config.markdown_description
    assert config.full_output == "llms-full.txt"
    assert "Getting Started" in config.sections
    assert config.sections["Getting Started"] == ["index.md", "install.md"]


def test_load_config_nav_fallback():
    config = load_config(FIXTURES / "mkdocs_nav_only.yml")

    assert config.site_name == "Test Site"
    # Sections derived from nav
    assert "Home" in config.sections or "Guide" in config.sections


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/mkdocs.yml"))


def test_get_page_title():
    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

    assert config.get_page_title("index.md") == "Home"
    assert config.get_page_title("install.md") == "Install"
    # Fallback for unknown pages
    assert "unknown" in config.get_page_title("unknown-page.md").lower()
