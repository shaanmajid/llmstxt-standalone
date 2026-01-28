"""Main generation orchestration."""

from __future__ import annotations

from pathlib import Path

from llmstxt_standalone.config import Config
from llmstxt_standalone.convert import html_to_markdown


def md_path_to_html_path(
    site_dir: Path, md_path: str, use_directory_urls: bool = True
) -> Path:
    """Convert docs/foo.md path to site HTML path.

    Args:
        site_dir: Path to the built site directory.
        md_path: Relative markdown file path (e.g., "install.md").
        use_directory_urls: If True, maps to foo/index.html; if False, maps to foo.html.

    Returns:
        Path to the corresponding HTML file.
    """
    if md_path == "index.md":
        return site_dir / "index.html"
    if use_directory_urls:
        return site_dir / md_path.replace(".md", "") / "index.html"
    return site_dir / md_path.replace(".md", ".html")


def md_path_to_md_url(site_url: str, md_path: str) -> str:
    """Convert docs/foo.md path to HTML page URL on the deployed site."""
    if md_path == "index.md":
        return f"{site_url}/"
    return f"{site_url}/{md_path.replace('.md', '')}/"


def generate_llms_txt(
    config: Config,
    site_dir: Path,
    verbose: bool = False,
) -> tuple[str, str]:
    """Generate llms.txt and llms-full.txt content.

    Args:
        config: Resolved configuration.
        site_dir: Path to built HTML site directory.
        verbose: Whether to print progress.

    Returns:
        Tuple of (llms_txt content, llms_full_txt content).
    """
    # Build llms.txt (index)
    llms_lines = [f"# {config.site_name}", ""]

    if config.site_description:
        llms_lines.append(f"> {config.site_description}")
        llms_lines.append("")

    if config.markdown_description:
        llms_lines.append(config.markdown_description.strip())
        llms_lines.append("")

    # Build llms-full.txt header
    full_lines = [f"# {config.site_name}", ""]

    if config.site_description:
        full_lines.append(f"> {config.site_description}")
        full_lines.append("")

    # Process sections
    all_pages: list[tuple[str, str]] = []

    for section_name, pages in config.sections.items():
        llms_lines.append(f"## {section_name}")
        llms_lines.append("")

        for page in pages:
            title = config.get_page_title(page)
            md_url = md_path_to_md_url(config.site_url, page)
            llms_lines.append(f"- [{title}]({md_url})")
            all_pages.append((title, page))

        llms_lines.append("")

    # Convert pages for llms-full.txt
    for title, md_path in all_pages:
        html_path = md_path_to_html_path(site_dir, md_path, config.use_directory_urls)

        if not html_path.exists():
            if verbose:
                print(f"Warning: {html_path} not found, skipping")
            continue

        html = html_path.read_text(encoding="utf-8")
        content = html_to_markdown(html, config.content_selector)

        if content:
            full_lines.append(f"## {title}")
            full_lines.append("")
            full_lines.append(content)
            full_lines.append("")

    llms_txt = "\n".join(llms_lines)
    llms_full_txt = "\n".join(full_lines)

    return llms_txt, llms_full_txt
