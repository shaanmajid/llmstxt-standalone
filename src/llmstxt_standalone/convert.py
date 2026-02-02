"""HTML to Markdown conversion."""

from __future__ import annotations

import mdformat
from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import ATX, MarkdownConverter


def _should_remove(tag: Tag) -> bool:
    """Check if a tag should be removed during autoclean."""
    if tag.name in {"img", "svg"}:
        return True
    if tag.name == "a" and tag.img:
        return True
    classes = tag.get("class") or ()
    if tag.name == "a" and "headerlink" in classes:
        return True
    if "twemoji" in classes:
        return True
    return "tabbed-labels" in classes


def _autoclean(soup: BeautifulSoup | Tag) -> None:
    """Remove unwanted elements from HTML."""
    for element in soup.find_all(_should_remove):
        element.decompose()

    # Unwrap autoref elements
    for element in soup.find_all("autoref"):
        element.replace_with(NavigableString(element.get_text()))

    # Remove line numbers from code blocks
    for element in soup.find_all("table", attrs={"class": "highlighttable"}):
        code = element.find("code")
        if code:
            # Find the root BeautifulSoup document to create new tags
            # (soup parameter may be a Tag, which doesn't have new_tag)
            doc = next(
                (p for p in element.parents if isinstance(p, BeautifulSoup)), None
            )
            if doc:
                pre_tag = doc.new_tag("pre")
                pre_tag.string = code.get_text()
                element.replace_with(pre_tag)


def _get_language(tag: Tag) -> str:
    """Extract language from code block classes.

    The callback receives the <pre> tag, so we need to check:
    1. Classes on the <pre> tag itself
    2. Classes on the parent of <pre>
    3. Classes on child <code> element (common pattern: <pre><code class="language-X">)
    """
    classes: list[str] = list(tag.get("class") or ())

    # Check parent classes
    if tag.parent:
        classes.extend(tag.parent.get("class") or ())

    # Check child <code> element classes
    code_child = tag.find("code")
    if code_child:
        classes.extend(code_child.get("class") or ())

    for css_class in classes:
        if css_class.startswith("language-"):
            return css_class[9:]
    return ""


# Converter with mkdocs-llmstxt-compatible settings
_converter = MarkdownConverter(
    bullets="-",
    code_language_callback=_get_language,
    escape_underscores=False,
    heading_style=ATX,
)


def extract_title_from_html(html: str, site_name: str | None = None) -> str | None:
    """Extract page title from HTML.

    Tries <title> tag first, then falls back to first <h1>.
    Strips site name suffixes (e.g., "Page - Site Name" -> "Page") when provided.

    Args:
        html: Raw HTML content.
        site_name: Site name to strip from title suffixes (e.g., "Page - Site").

    Returns:
        The page title, or None if not found.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try <title> tag first
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text().strip()
        # Strip site name suffix only when it matches the configured site name.
        if site_name and " - " in title:
            base, suffix = title.rsplit(" - ", 1)
            if suffix.strip().casefold() == site_name.strip().casefold():
                title = base.strip()
        if title:
            return title

    # Fall back to first <h1>
    h1_tag = soup.find("h1")
    if h1_tag:
        text = h1_tag.get_text().strip()
        if text:
            return text

    return None


def html_to_markdown(html: str, content_selector: str | None = None) -> str:
    """Convert HTML to clean Markdown.

    Args:
        html: Raw HTML content.
        content_selector: Optional CSS selector for main content.
            Defaults to Material for MkDocs selectors.

    Returns:
        Cleaned Markdown text.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find main content
    if content_selector:
        try:
            content = soup.select_one(content_selector)
        except Exception:
            content = None
        else:
            if content is None:
                return ""
    else:
        content = None

    if content is None:
        content = (
            soup.select_one(".md-content__inner")  # Material for MkDocs
            or soup.select_one('[role="main"]')  # Default MkDocs theme
            or soup.select_one("article")
            or soup.select_one("main")
            or soup
        )

    if content is None:
        return ""

    _autoclean(content)
    md = _converter.convert_soup(content)
    return mdformat.text(md, options={"wrap": "no"}, extensions=("tables",))
