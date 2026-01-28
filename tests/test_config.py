"""Tests for configuration loading."""

from pathlib import Path

import pytest

from llmstxt_standalone.config import load_config

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
    # Default: use_directory_urls is True when not specified
    assert config.use_directory_urls is True


def test_load_config_use_directory_urls_false():
    config = load_config(FIXTURES / "mkdocs_no_directory_urls.yml")

    assert config.site_name == "Test Site"
    assert config.use_directory_urls is False


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


def test_yaml_types_parsed_correctly():
    """Verify that YAML null, boolean, and numeric values are parsed as proper types."""
    config = load_config(FIXTURES / "mkdocs_with_yaml_types.yml")

    # null should be None, not the string "null"
    assert config.content_selector is None
    assert config.content_selector != "null"


def test_load_config_mapping_style_plugins():
    """Test that mapping-style plugins config is handled correctly.

    MkDocs supports both list and mapping styles for plugins:
    - List: plugins: [- llmstxt: {...}]
    - Mapping: plugins: {llmstxt: {...}}
    """
    config = load_config(FIXTURES / "mkdocs_mapping_plugins.yml")

    assert config.site_name == "Test Site"
    assert config.site_description == "A test site with mapping-style plugins"
    assert config.site_url == "https://test.com"
    assert "Custom description" in config.markdown_description
    assert config.full_output == "llms-full.txt"
    assert "Getting Started" in config.sections
    assert config.sections["Getting Started"] == ["index.md", "install.md"]
