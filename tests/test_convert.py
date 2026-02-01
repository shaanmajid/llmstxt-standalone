"""Tests for HTML to Markdown conversion."""

import pytest

from llmstxt_standalone.convert import extract_title_from_html, html_to_markdown


def test_html_to_markdown_basic():
    html = """
    <article>
        <h1>Title</h1>
        <p>This is <strong>bold</strong> text.</p>
    </article>
    """
    result = html_to_markdown(html)
    assert "# Title" in result
    assert "**bold**" in result


def test_html_to_markdown_removes_images():
    html = """
    <article>
        <p>Text</p>
        <img src="test.png" alt="test">
    </article>
    """
    result = html_to_markdown(html)
    assert "img" not in result.lower()
    assert "test.png" not in result


def test_html_to_markdown_removes_headerlinks():
    html = """
    <article>
        <h2>Section<a href="#section" class="headerlink">¶</a></h2>
    </article>
    """
    result = html_to_markdown(html)
    assert "¶" not in result
    assert "headerlink" not in result


def test_html_to_markdown_preserves_code_language():
    html = """
    <article>
        <pre><code class="language-python">print("hello")</code></pre>
    </article>
    """
    result = html_to_markdown(html)
    assert "```python" in result
    assert 'print("hello")' in result


def test_html_to_markdown_default_mkdocs_theme():
    """Test that [role="main"] selector works for default MkDocs theme."""
    html = """
    <html>
    <body>
    <nav class="navbar"><a href="/">Home</a></nav>
    <div class="col-md-9" role="main">
        <h1>Main Content</h1>
        <p>This should be extracted.</p>
    </div>
    <footer>Footer</footer>
    </body>
    </html>
    """
    result = html_to_markdown(html)
    assert "# Main Content" in result
    assert "This should be extracted" in result
    assert "navbar" not in result.lower()
    assert "Footer" not in result


@pytest.mark.parametrize(
    ("html", "expected", "site_name"),
    [
        (
            """
            <html>
            <head><title>Page Title</title></head>
            <body><h1>Different H1</h1></body>
            </html>
            """,
            "Page Title",
            None,
        ),
        # " - " separator (common pattern)
        (
            """
            <html>
            <head><title>Page Title - My Site</title></head>
            <body></body>
            </html>
            """,
            "Page Title",
            "My Site",
        ),
        (
            "<html><head><title>API - Authentication - My Site</title></head></html>",
            "API - Authentication",
            "My Site",
        ),
        (
            "<html><head><title>API - Authentication</title></head></html>",
            "API - Authentication",
            "My Site",
        ),
        # " | " separator (Material for MkDocs default)
        (
            "<html><head><title>Installation | uv</title></head></html>",
            "Installation",
            "uv",
        ),
        (
            "<html><head><title>API - Authentication | My Site</title></head></html>",
            "API - Authentication",
            "My Site",
        ),
        (
            "<html><head><title>Page | Other Site</title></head></html>",
            "Page | Other Site",  # Should NOT strip when site_name doesn't match
            "My Site",
        ),
        (
            """<html><head><title>
                Page Title
            </title></head></html>""",
            "Page Title",
            None,
        ),
        (
            "<html><head><title>AT&amp;T &amp; Verizon</title></head></html>",
            "AT&T & Verizon",
            None,
        ),
    ],
)
def test_extract_title_from_html_title_tag_cases(
    html: str, expected: str, site_name: str | None
):
    """Test title extraction from <title> tag across common patterns."""
    assert extract_title_from_html(html, site_name=site_name) == expected


def test_extract_title_from_html_fallback_to_h1():
    """Test that H1 is used when no title tag exists."""
    html = """
    <html>
    <body><h1>Heading One</h1></body>
    </html>
    """
    assert extract_title_from_html(html) == "Heading One"


def test_extract_title_from_html_returns_none_when_no_title():
    """Test that None is returned when no title can be found."""
    html = "<html><body><p>Just a paragraph</p></body></html>"
    assert extract_title_from_html(html) is None


def test_extract_title_from_html_empty_h1():
    """Test that whitespace-only H1 returns None, not empty string."""
    html = "<html><body><h1>   </h1></body></html>"
    assert extract_title_from_html(html) is None
