"""Main generation orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from llmstxt_standalone.config import Config
from llmstxt_standalone.convert import extract_title_from_html, html_to_markdown


def _escape_markdown_link_text(text: str) -> str:
    """Escape characters that break markdown link syntax.

    Args:
        text: The link text to escape.

    Returns:
        Text with [ and ] escaped as \\[ and \\].
    """
    return text.replace("[", r"\[").replace("]", r"\]")


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
    # Handle index.md at any level (root or nested like foo/bar/index.md)
    if md_path == "index.md" or md_path.endswith("/index.md"):
        return site_dir / md_path.replace(".md", ".html")
    if use_directory_urls:
        return site_dir / md_path.replace(".md", "") / "index.html"
    return site_dir / md_path.replace(".md", ".html")


def md_path_to_page_url(
    site_url: str,
    md_path: str,
    use_directory_urls: bool = True,
) -> str:
    """Convert docs/foo.md path to markdown file URL on the deployed site.

    Args:
        site_url: Base URL of the site.
        md_path: Relative markdown file path (e.g., "install.md").
        use_directory_urls: If True, directory-style URLs; if False, flat URLs.

    Returns:
        URL to the markdown file on the deployed site.
    """
    if not site_url:
        if md_path == "index.md" or md_path.endswith("/index.md"):
            return md_path
        if use_directory_urls:
            return md_path.replace(".md", "") + "/index.md"
        return md_path
    # Handle index.md at any level (root or nested like foo/bar/index.md)
    if md_path == "index.md" or md_path.endswith("/index.md"):
        return f"{site_url}/{md_path}"
    if use_directory_urls:
        return f"{site_url}/{md_path.replace('.md', '')}/index.md"
    return f"{site_url}/{md_path}"


def md_path_to_output_md_path(
    site_dir: Path, md_path: str, use_directory_urls: bool = True
) -> Path:
    """Convert docs/foo.md path to site markdown output path.

    Args:
        site_dir: Path to the built site directory.
        md_path: Relative markdown file path (e.g., "install.md").
        use_directory_urls: If True, outputs to foo/index.md; if False, outputs to foo.md.

    Returns:
        Path where the markdown file should be written.
    """
    # Handle index.md at any level (root or nested like foo/bar/index.md)
    if md_path == "index.md" or md_path.endswith("/index.md"):
        return site_dir / md_path
    if use_directory_urls:
        return site_dir / md_path.replace(".md", "") / "index.md"
    return site_dir / md_path


@dataclass
class PageMarkdown:
    """Per-page markdown output."""

    md_path: str
    content: str


@dataclass
class BuildResult:
    """Result of building llms.txt content (no files written)."""

    llms_txt: str
    llms_full_txt: str
    pages: list[PageMarkdown]
    skipped: list[tuple[Path, str]]
    warnings: list[str]


@dataclass
class GenerateResult:
    """Result of llms.txt generation with files written."""

    llms_txt: str
    llms_full_txt: str
    markdown_files: list[Path]
    skipped: list[tuple[Path, str]]
    warnings: list[str]


def build_llms_output(
    config: Config,
    site_dir: Path,
) -> BuildResult:
    """Build llms.txt, llms-full.txt, and per-page markdown content.

    Args:
        config: Resolved configuration.
        site_dir: Path to built HTML site directory.

    Returns:
        BuildResult with content and per-page markdown data.
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

    # Process sections - check HTML existence and extract titles first
    page_outputs: list[PageMarkdown] = []
    skipped: list[tuple[Path, str]] = []
    warnings: list[str] = []

    for section_name, section_pages in config.sections.items():
        section_entries: list[str] = []

        for md_path in section_pages:
            html_path = md_path_to_html_path(
                site_dir, md_path, config.use_directory_urls
            )

            if not html_path.exists():
                skipped.append((html_path, "HTML file not found"))
                continue

            try:
                html = html_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                skipped.append((html_path, "HTML file has encoding errors"))
                continue

            # Extract title from HTML, fall back to config title
            title = extract_title_from_html(
                html, site_name=config.site_name
            ) or config.get_page_title(md_path)

            page_url = md_path_to_page_url(
                config.site_url,
                md_path,
                config.use_directory_urls,
            )
            # Escape brackets in title to produce valid markdown links
            escaped_title = _escape_markdown_link_text(title)
            section_entries.append(f"- [{escaped_title}]({page_url})")

            # Convert content for llms-full.txt
            content = html_to_markdown(html, config.content_selector)

            if content:
                full_lines.append(f"## {title}")
                full_lines.append("")
                full_lines.append(content)
                full_lines.append("")
            else:
                warning = (
                    f"No markdown content extracted from {html_path}; content empty"
                )
                warnings.append(warning)

            page_outputs.append(PageMarkdown(md_path=md_path, content=content))

        # Only add section to llms.txt if it has entries
        if section_entries:
            llms_lines.append(f"## {section_name}")
            llms_lines.append("")
            llms_lines.extend(section_entries)
            llms_lines.append("")

    llms_txt = "\n".join(llms_lines)
    llms_full_txt = "\n".join(full_lines)

    return BuildResult(
        llms_txt=llms_txt,
        llms_full_txt=llms_full_txt,
        pages=page_outputs,
        skipped=skipped,
        warnings=warnings,
    )


def write_markdown_files(
    pages: list[PageMarkdown],
    output_dir: Path,
    use_directory_urls: bool,
    dry_run: bool = False,
) -> list[Path]:
    """Write per-page markdown files to disk.

    Args:
        pages: Per-page markdown content.
        output_dir: Path to write output files.
        use_directory_urls: If True, outputs to foo/index.md; if False, outputs to foo.md.
        dry_run: If True, don't write markdown files.

    Returns:
        List of output markdown paths (written or would-be).
    """
    markdown_files: list[Path] = []
    for page in pages:
        output_md_path = md_path_to_output_md_path(
            output_dir, page.md_path, use_directory_urls
        )
        if not dry_run:
            output_md_path.parent.mkdir(parents=True, exist_ok=True)
            output_md_path.write_text(page.content, encoding="utf-8")
        markdown_files.append(output_md_path)
    return markdown_files


def generate_llms_txt(
    config: Config,
    site_dir: Path,
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> GenerateResult:
    """Generate llms.txt, llms-full.txt, and per-page markdown files.

    Args:
        config: Resolved configuration.
        site_dir: Path to built HTML site directory.
        output_dir: Path to write output files. Defaults to site_dir.
        dry_run: If True, don't write markdown files.
    Returns:
        GenerateResult with content and list of markdown files (written or would-be).
    """
    build = build_llms_output(config=config, site_dir=site_dir)
    if output_dir is None:
        output_dir = site_dir
    markdown_files = write_markdown_files(
        build.pages,
        output_dir=output_dir,
        use_directory_urls=config.use_directory_urls,
        dry_run=dry_run,
    )

    return GenerateResult(
        llms_txt=build.llms_txt,
        llms_full_txt=build.llms_full_txt,
        markdown_files=markdown_files,
        skipped=build.skipped,
        warnings=build.warnings,
    )
