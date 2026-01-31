"""Tests for generation orchestration."""

import shutil
from pathlib import Path

from llmstxt_standalone.config import load_config
from llmstxt_standalone.generate import (
    generate_llms_txt,
    md_path_to_html_path,
    md_path_to_output_md_path,
    md_path_to_page_url,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_md_path_to_html_path_with_directory_urls():
    """Test path conversion when use_directory_urls is True (default)."""
    site_dir = Path("/site")

    assert md_path_to_html_path(site_dir, "index.md") == Path("/site/index.html")
    assert md_path_to_html_path(site_dir, "install.md") == Path(
        "/site/install/index.html"
    )
    assert md_path_to_html_path(site_dir, "guide/intro.md") == Path(
        "/site/guide/intro/index.html"
    )
    # Explicit True
    assert md_path_to_html_path(
        site_dir, "install.md", use_directory_urls=True
    ) == Path("/site/install/index.html")
    # Nested index.md files should NOT double up index/index.html
    assert md_path_to_html_path(site_dir, "concepts/auth/index.md") == Path(
        "/site/concepts/auth/index.html"
    )


def test_md_path_to_html_path_without_directory_urls():
    """Test path conversion when use_directory_urls is False."""
    site_dir = Path("/site")

    # index.md always maps to index.html regardless of setting
    assert md_path_to_html_path(site_dir, "index.md", use_directory_urls=False) == Path(
        "/site/index.html"
    )
    # Other pages map to foo.html instead of foo/index.html
    assert md_path_to_html_path(
        site_dir, "install.md", use_directory_urls=False
    ) == Path("/site/install.html")
    assert md_path_to_html_path(
        site_dir, "guide/intro.md", use_directory_urls=False
    ) == Path("/site/guide/intro.html")


def test_md_path_to_page_url_with_directory_urls():
    """Test URL generation when use_directory_urls is True (default)."""
    site_url = "https://example.com"

    # Always generates markdown URLs
    assert md_path_to_page_url(site_url, "index.md") == "https://example.com/index.md"
    assert (
        md_path_to_page_url(site_url, "install.md")
        == "https://example.com/install/index.md"
    )
    assert (
        md_path_to_page_url(site_url, "guide/intro.md")
        == "https://example.com/guide/intro/index.md"
    )
    # Nested index.md files should NOT double up index/index.md
    assert (
        md_path_to_page_url(site_url, "concepts/auth/index.md")
        == "https://example.com/concepts/auth/index.md"
    )


def test_md_path_to_page_url_without_directory_urls():
    """Test URL generation when use_directory_urls is False."""
    site_url = "https://example.com"

    # index.md always maps to /index.md
    assert (
        md_path_to_page_url(site_url, "index.md", use_directory_urls=False)
        == "https://example.com/index.md"
    )
    # Other pages map to foo.md (flat structure)
    assert (
        md_path_to_page_url(site_url, "install.md", use_directory_urls=False)
        == "https://example.com/install.md"
    )
    assert (
        md_path_to_page_url(site_url, "guide/intro.md", use_directory_urls=False)
        == "https://example.com/guide/intro.md"
    )


def test_md_path_to_page_url_without_site_url():
    """Test URL generation when site_url is empty."""
    site_url = ""

    # Directory URLs default
    assert md_path_to_page_url(site_url, "index.md") == "index.md"
    assert md_path_to_page_url(site_url, "install.md") == "install/index.md"
    assert md_path_to_page_url(site_url, "guide/intro.md") == "guide/intro/index.md"
    assert (
        md_path_to_page_url(site_url, "concepts/auth/index.md")
        == "concepts/auth/index.md"
    )

    # Flat URLs
    assert (
        md_path_to_page_url(site_url, "install.md", use_directory_urls=False)
        == "install.md"
    )


def test_md_path_to_output_md_path():
    """Test markdown output path generation."""
    site_dir = Path("/site")

    # With directory URLs (default)
    assert md_path_to_output_md_path(site_dir, "index.md") == Path("/site/index.md")
    assert md_path_to_output_md_path(site_dir, "install.md") == Path(
        "/site/install/index.md"
    )
    assert md_path_to_output_md_path(site_dir, "guide/intro.md") == Path(
        "/site/guide/intro/index.md"
    )
    # Nested index.md files should NOT double up index/index.md
    assert md_path_to_output_md_path(site_dir, "concepts/auth/index.md") == Path(
        "/site/concepts/auth/index.md"
    )

    # Without directory URLs
    assert md_path_to_output_md_path(
        site_dir, "install.md", use_directory_urls=False
    ) == Path("/site/install.md")


def test_generate_llms_txt(tmp_path: Path):
    """Test that llms.txt, llms-full.txt, and markdown files are generated."""

    # Copy fixture site to temp directory so we can write to it
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)

    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
    )

    # Check llms.txt structure
    assert "# Test Site" in result.llms_txt
    assert "> A test site" in result.llms_txt
    assert "Custom description" in result.llms_txt
    assert "## Getting Started" in result.llms_txt
    assert "[Home](" in result.llms_txt

    # Check that URLs point to .md files
    assert "/index.md" in result.llms_txt

    # Check llms-full.txt structure
    assert "# Test Site" in result.llms_full_txt
    assert "Welcome" in result.llms_full_txt or "Installation" in result.llms_full_txt

    # Check that markdown files were written
    assert len(result.markdown_files) > 0
    for md_file in result.markdown_files:
        assert md_file.exists()
        content = md_file.read_text()
        assert len(content) > 0


def test_generate_llms_txt_dry_run(tmp_path: Path):
    """Test that dry_run=True doesn't write markdown files."""

    # Copy fixture site to temp directory
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)

    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
        dry_run=True,
    )

    # Content is still generated
    assert "# Test Site" in result.llms_txt
    assert len(result.markdown_files) > 0

    # But files are not actually written
    for md_file in result.markdown_files:
        assert not md_file.exists()


def test_generate_llms_txt_empty_content_warns_and_writes(tmp_path: Path):
    """Test that empty extraction warns and still writes empty markdown files."""

    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)

    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")
    config.content_selector = ".does-not-exist"

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
    )

    assert len(result.warnings) >= 1
    assert "/index.md" in result.llms_txt
    assert len(result.markdown_files) > 0
    for md_file in result.markdown_files:
        assert md_file.exists()
        assert md_file.read_text(encoding="utf-8") == ""


def test_generate_llms_txt_unicode_and_special_chars(tmp_path: Path):
    """Test handling of unicode characters, emojis, and special chars."""

    # Copy edge case fixture site to temp directory
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site_edge_cases", site_dir)

    config = load_config(FIXTURES / "mkdocs_edge_cases.yml")

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
    )

    # Check unicode in site name and description
    assert "Édge Çases" in result.llms_txt
    assert "日本語" in result.llms_txt

    # Check unicode in markdown description
    assert "spëcial characters" in result.llms_txt
    assert "🚀" in result.llms_txt

    # Check unicode section names
    assert "Getting Started 🚀" in result.llms_txt
    assert "深层文档" in result.llms_txt

    # Check content with special chars is preserved
    assert (
        "Hello 世界" in result.llms_full_txt or "Welcome 日本語" in result.llms_full_txt
    )

    # Check markdown files were written correctly
    assert len(result.markdown_files) > 0
    for md_file in result.markdown_files:
        assert md_file.exists()
        content = md_file.read_text(encoding="utf-8")
        assert len(content) > 0


def test_generate_llms_txt_uses_html_titles(tmp_path: Path):
    """Test that page titles are extracted from HTML <title> tags, not nav paths."""

    # Copy fixture site to temp directory
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)

    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
    )

    # Titles should come from HTML <title> tags, not nav paths
    # The fixture site/index.html has <title>Home</title>
    # The fixture site/install/index.html has <title>Install</title>
    assert "[Home](" in result.llms_txt
    assert "[Install](" in result.llms_txt

    # Should NOT contain fallback-style titles like "Index" or path-derived titles
    assert "[Index](" not in result.llms_txt


def test_generate_llms_txt_skips_missing_pages(tmp_path: Path):
    """Test that pages without HTML files are skipped from llms.txt entirely."""

    # Copy fixture site to temp directory
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)

    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

    # Add a non-existent page to the config
    config.sections["Getting Started"].append("nonexistent.md")

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
    )

    # The non-existent page should NOT appear in llms.txt
    assert "nonexistent" not in result.llms_txt.lower()
    # But existing pages should still be there
    assert "[Home](" in result.llms_txt


def test_generate_llms_txt_html_title_overrides_nav(tmp_path: Path):
    """Test that HTML <title> overrides nav-derived title when they differ."""

    # Copy fixture site to temp directory
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)

    # Create an HTML file with a different title than nav would suggest
    deep_dir = site_dir / "deep" / "nested"
    deep_dir.mkdir(parents=True, exist_ok=True)
    (deep_dir / "index.html").write_text(
        """<!DOCTYPE html>
        <html>
        <head><title>Authentication</title></head>
        <body><article><h1>Authentication</h1><p>Content</p></article></body>
        </html>
        """,
        encoding="utf-8",
    )

    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")
    # Add the deep nested page - nav would derive "Deep - Nested - Index"
    config.sections["Getting Started"].append("deep/nested/index.md")

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
    )

    # Should use HTML title "Authentication", not nav-derived "Deep - Nested - Index"
    assert "[Authentication](" in result.llms_txt
    assert "Deep - Nested" not in result.llms_txt


def test_generate_llms_txt_escapes_brackets_in_titles(tmp_path: Path):
    """Test that brackets in titles are escaped to produce valid markdown links."""

    # Copy fixture site to temp directory
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)

    # Create an HTML file with brackets in the title
    api_dir = site_dir / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "index.html").write_text(
        """<!DOCTYPE html>
        <html>
        <head><title>API [v2] Reference</title></head>
        <body><article><h1>API [v2] Reference</h1><p>Content</p></article></body>
        </html>
        """,
        encoding="utf-8",
    )

    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")
    config.sections["Getting Started"].append("api/index.md")

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
    )

    # Brackets should be escaped so the markdown link is valid
    # [API \[v2\] Reference](url) instead of [API [v2] Reference](url)
    assert r"[API \[v2\] Reference](" in result.llms_txt
    # The unescaped version should NOT appear
    assert "[API [v2] Reference](" not in result.llms_txt


def test_generate_llms_txt_skips_encoding_errors(tmp_path: Path):
    """Test that files with encoding errors are skipped gracefully."""

    # Copy fixture site to temp directory
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)

    # Create an HTML file with invalid UTF-8 bytes
    bad_dir = site_dir / "bad"
    bad_dir.mkdir(parents=True, exist_ok=True)
    (bad_dir / "index.html").write_bytes(
        b"<!DOCTYPE html><html><head><title>Bad</title></head>"
        b"<body>\xff\xfe Invalid UTF-8</body></html>"
    )

    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")
    config.sections["Getting Started"].append("bad/index.md")

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
    )

    # The bad page should be skipped (not crash, not appear in output)
    assert "Bad" not in result.llms_txt
    # But existing pages should still be there
    assert "[Home](" in result.llms_txt


def test_generate_llms_txt_respects_output_dir(tmp_path: Path):
    """Test that per-page markdown files go to output_dir when specified."""

    # Copy fixture site to temp directory
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)

    # Create a separate output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

    result = generate_llms_txt(
        config=config,
        site_dir=site_dir,
        output_dir=output_dir,
    )

    # Per-page markdown files should be in output_dir, NOT site_dir
    assert len(result.markdown_files) > 0
    for md_file in result.markdown_files:
        # All markdown files should be under output_dir
        assert str(md_file).startswith(str(output_dir))
        assert md_file.exists()

    # site_dir should NOT have the per-page markdown files
    # (only the original HTML files should be there)
    for md_file in result.markdown_files:
        # The equivalent path in site_dir should NOT exist
        relative = md_file.relative_to(output_dir)
        site_equivalent = site_dir / relative
        # The site_dir might have index.html but not index.md
        if site_equivalent.name == "index.md":
            html_equivalent = site_equivalent.with_suffix(".html")
            # HTML should exist, but markdown should not
            assert not site_equivalent.exists() or site_equivalent == html_equivalent
