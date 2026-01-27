"""Tests for generation orchestration."""

from pathlib import Path

from llmstxt_gen.config import load_config
from llmstxt_gen.generate import (
    generate_llms_txt,
    md_path_to_html_path,
    md_path_to_md_url,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_md_path_to_html_path():
    site_dir = Path("/site")

    assert md_path_to_html_path(site_dir, "index.md") == Path("/site/index.html")
    assert md_path_to_html_path(site_dir, "install.md") == Path(
        "/site/install/index.html"
    )
    assert md_path_to_html_path(site_dir, "guide/intro.md") == Path(
        "/site/guide/intro/index.html"
    )


def test_md_path_to_md_url():
    site_url = "https://example.com"

    assert md_path_to_md_url(site_url, "index.md") == "https://example.com/index.md"
    assert (
        md_path_to_md_url(site_url, "install.md")
        == "https://example.com/install/index.md"
    )


def test_generate_llms_txt(tmp_path: Path):
    config = load_config(FIXTURES / "mkdocs_with_llmstxt.yml")

    llms_txt, llms_full_txt = generate_llms_txt(
        config=config,
        site_dir=FIXTURES / "site",
    )

    # Check llms.txt structure
    assert "# Test Site" in llms_txt
    assert "> A test site" in llms_txt
    assert "Custom description" in llms_txt
    assert "## Getting Started" in llms_txt
    assert "[Home](" in llms_txt

    # Check llms-full.txt structure
    assert "# Test Site" in llms_full_txt
    assert "Welcome" in llms_full_txt or "Installation" in llms_full_txt
