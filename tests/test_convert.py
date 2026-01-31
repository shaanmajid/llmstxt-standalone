"""Tests for HTML to Markdown conversion."""

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


def test_extract_title_from_html_uses_title_tag():
    """Test that title is extracted from <title> tag."""
    html = """
    <html>
    <head><title>Page Title</title></head>
    <body><h1>Different H1</h1></body>
    </html>
    """
    assert extract_title_from_html(html) == "Page Title"


def test_extract_title_from_html_strips_site_suffix():
    """Test that site name suffix is stripped from title."""
    html = """
    <html>
    <head><title>Page Title - My Site</title></head>
    <body></body>
    </html>
    """
    # Should return just the page title, not "Page Title - My Site"
    assert extract_title_from_html(html) == "Page Title"


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


def test_extract_title_from_html_multiple_dashes():
    """Test that only the last dash-separated segment is stripped."""
    html = "<html><head><title>API - Authentication - My Site</title></head></html>"
    # Should preserve "API - Authentication", only strip " - My Site"
    assert extract_title_from_html(html) == "API - Authentication"


def test_extract_title_from_html_multiline_title():
    """Test title extraction when title spans multiple lines."""
    html = """<html><head><title>
        Page Title
    </title></head></html>"""
    assert extract_title_from_html(html) == "Page Title"


def test_extract_title_from_html_empty_h1():
    """Test that whitespace-only H1 returns None, not empty string."""
    html = "<html><body><h1>   </h1></body></html>"
    assert extract_title_from_html(html) is None


def test_extract_title_from_html_entities():
    """Test that HTML entities are decoded properly."""
    html = "<html><head><title>AT&amp;T &amp; Verizon</title></head></html>"
    assert extract_title_from_html(html) == "AT&T & Verizon"
