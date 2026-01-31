"""Tests for robustness fixes: path traversal, selector errors, I/O errors."""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from llmstxt_standalone.config import load_config
from llmstxt_standalone.convert import html_to_markdown
from llmstxt_standalone.generate import (
    generate_llms_txt,
    md_path_to_html_path,
    md_path_to_output_md_path,
)

FIXTURES = Path(__file__).parent / "fixtures"


# =============================================================================
# Path Traversal Protection Tests
# =============================================================================


class TestPathTraversalProtection:
    """Tests that path traversal attacks are rejected."""

    def test_md_path_to_html_path_rejects_absolute_path(self):
        """Absolute paths should be rejected."""
        site_dir = Path("/site")
        with pytest.raises(ValueError, match="relative"):
            md_path_to_html_path(site_dir, "/etc/passwd.md")

    def test_md_path_to_html_path_rejects_parent_traversal(self):
        """Paths with .. should be rejected."""
        site_dir = Path("/site")
        with pytest.raises(ValueError, match="\\.\\."):
            md_path_to_html_path(site_dir, "../etc/passwd.md")

    def test_md_path_to_html_path_rejects_nested_traversal(self):
        """Nested paths with .. should be rejected."""
        site_dir = Path("/site")
        with pytest.raises(ValueError, match="\\.\\."):
            md_path_to_html_path(site_dir, "docs/../../../etc/passwd.md")

    def test_md_path_to_output_md_path_rejects_absolute_path(self):
        """Absolute paths should be rejected for output paths."""
        site_dir = Path("/site")
        with pytest.raises(ValueError, match="relative"):
            md_path_to_output_md_path(site_dir, "/etc/passwd.md")

    def test_md_path_to_output_md_path_rejects_parent_traversal(self):
        """Paths with .. should be rejected for output paths."""
        site_dir = Path("/site")
        with pytest.raises(ValueError, match="\\.\\."):
            md_path_to_output_md_path(site_dir, "../etc/passwd.md")

    def test_generate_skips_traversal_paths(self, tmp_path: Path):
        """Generation should skip paths that attempt traversal."""
        site_dir = tmp_path / "site"
        shutil.copytree(FIXTURES / "site", site_dir)

        config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")
        # Inject a malicious path
        config.sections["Getting Started"].append("../../../etc/passwd.md")

        result = generate_llms_txt(
            config=config,
            site_dir=site_dir,
        )

        # The traversal path should be skipped, not crash
        # and should not appear in output
        assert "passwd" not in result.llms_txt.lower()
        # But valid pages should still work
        assert "[Home](" in result.llms_txt


# =============================================================================
# CSS Selector Error Handling Tests
# =============================================================================


class TestCssSelectorErrorHandling:
    """Tests that invalid CSS selectors are handled gracefully."""

    def test_html_to_markdown_invalid_selector_falls_back_to_defaults(self):
        """Invalid CSS selector should not crash, should fall back to defaults."""
        html = """
        <html>
        <body>
        <article><h1>Title</h1><p>Content</p></article>
        </body>
        </html>
        """
        # This is an invalid CSS selector that will raise an exception
        result = html_to_markdown(html, content_selector="[[[invalid")
        # Should not crash, should fall back to default selectors (finds <article>)
        assert "# Title" in result
        assert "Content" in result

    def test_html_to_markdown_nonexistent_selector_returns_empty(self):
        """Selector that matches nothing should return empty."""
        html = """
        <html>
        <body>
        <article><h1>Title</h1><p>Content</p></article>
        </body>
        </html>
        """
        result = html_to_markdown(html, content_selector=".does-not-exist")
        assert result == ""

    def test_html_to_markdown_valid_selector_works(self):
        """Valid selector should still work normally."""
        html = """
        <html>
        <body>
        <div class="custom-content"><h1>Title</h1><p>Content</p></div>
        <footer>Footer</footer>
        </body>
        </html>
        """
        result = html_to_markdown(html, content_selector=".custom-content")
        assert "# Title" in result
        assert "Content" in result
        assert "Footer" not in result


# =============================================================================
# I/O Error Handling Tests
# =============================================================================


class TestIOErrorHandling:
    """Tests that I/O errors are handled gracefully."""

    def test_generate_handles_html_read_oserror(self, tmp_path: Path):
        """OSError when reading HTML should skip the page, not crash."""
        site_dir = tmp_path / "site"
        shutil.copytree(FIXTURES / "site", site_dir)

        config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

        # Mock read_text to raise OSError for a specific file
        original_read_text = Path.read_text

        def mock_read_text(self, *args, **kwargs):
            if "index.html" in str(self) and "install" in str(self):
                raise OSError("Permission denied")
            return original_read_text(self, *args, **kwargs)

        with patch.object(Path, "read_text", mock_read_text):
            result = generate_llms_txt(
                config=config,
                site_dir=site_dir,
            )

        # Should not crash, should skip the problematic file
        # Home page should still be there
        assert "[Home](" in result.llms_txt

    def test_generate_handles_markdown_conversion_error(self, tmp_path: Path):
        """Error during markdown conversion should warn, not crash."""
        site_dir = tmp_path / "site"
        shutil.copytree(FIXTURES / "site", site_dir)

        config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

        # Mock html_to_markdown to raise an exception
        with patch(
            "llmstxt_standalone.generate.html_to_markdown",
            side_effect=Exception("Conversion failed"),
        ):
            result = generate_llms_txt(
                config=config,
                site_dir=site_dir,
            )

        # Should have warnings about the conversion failures
        assert len(result.warnings) > 0
        # Links should still be generated (even if full content is missing)
        assert "index.md" in result.llms_txt
