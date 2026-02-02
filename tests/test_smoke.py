"""Smoke tests for end-to-end CLI functionality.

These tests actually invoke the CLI and verify it produces valid output.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def site_copy(tmp_path: Path) -> Path:
    """Copy the test site fixture to a temporary directory."""
    site_dir = tmp_path / "site"
    shutil.copytree(FIXTURES / "site", site_dir)
    return tmp_path


def test_smoke_cli_subprocess(site_copy: Path) -> None:
    """End-to-end test: run llmstxt-standalone as subprocess and verify output."""
    site_dir = site_copy / "site"
    config_path = FIXTURES / "mkdocs_with_llmstxt.yml"

    # Run the CLI as a subprocess
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "llmstxt_standalone.cli",
            "--config",
            str(config_path),
            "--site-dir",
            str(site_dir),
            "--output-dir",
            str(site_dir),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Verify successful execution
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert "Generated" in result.stdout

    # Verify llms.txt was created
    llms_txt_path = site_dir / "llms.txt"
    assert llms_txt_path.exists(), "llms.txt was not created"
    llms_content = llms_txt_path.read_text(encoding="utf-8")

    # Verify llms.txt has expected structure
    assert "# Test Site" in llms_content, "Missing site name in llms.txt"
    assert "Custom description for LLMs" in llms_content, "Missing description"
    assert "## Getting Started" in llms_content, "Missing section header"

    # Verify llms-full.txt was created
    llms_full_path = site_dir / "llms-full.txt"
    assert llms_full_path.exists(), "llms-full.txt was not created"
    full_content = llms_full_path.read_text(encoding="utf-8")

    # Verify llms-full.txt contains actual page content
    assert "Welcome" in full_content, "Missing content from index.html"
    assert "Installation" in full_content, "Missing content from install page"
    assert "pip install example" in full_content, "Missing code block content"


def test_smoke_cli_verbose(site_copy: Path) -> None:
    """Test CLI verbose mode produces expected output."""
    site_dir = site_copy / "site"
    config_path = FIXTURES / "mkdocs_with_llmstxt.yml"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "llmstxt_standalone.cli",
            "--config",
            str(config_path),
            "--site-dir",
            str(site_dir),
            "--output-dir",
            str(site_dir),
            "--verbose",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    # Verbose mode should show site name and sections
    assert "Test Site" in result.stdout or "Site:" in result.stdout


def test_smoke_cli_version() -> None:
    """Test CLI version flag works."""
    result = subprocess.run(
        [sys.executable, "-m", "llmstxt_standalone.cli", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "llmstxt-standalone" in result.stdout


def test_smoke_cli_errors_on_empty_sections(site_copy: Path) -> None:
    """Test CLI errors when no sections are configured."""
    site_dir = site_copy / "site"
    config_path = FIXTURES / "mkdocs_no_nav.yml"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "llmstxt_standalone.cli",
            "--config",
            str(config_path),
            "--site-dir",
            str(site_dir),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 1, "CLI should exit with error when no sections"
    assert "No sections configured" in result.stderr
    assert "nav" in result.stderr.lower(), "Error should mention nav"


def test_smoke_output_content_structure(site_copy: Path) -> None:
    """Verify the output files have proper markdown structure."""
    site_dir = site_copy / "site"
    config_path = FIXTURES / "mkdocs_with_llmstxt.yml"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "llmstxt_standalone.cli",
            "--config",
            str(config_path),
            "--site-dir",
            str(site_dir),
            "--output-dir",
            str(site_dir),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )

    # Check llms.txt structure
    llms_content = (site_dir / "llms.txt").read_text(encoding="utf-8")
    lines = llms_content.strip().split("\n")

    # Should start with title
    assert lines[0].startswith("# "), "llms.txt should start with h1 title"

    # Should have description after title
    non_empty = [line for line in lines if line.strip()]
    assert len(non_empty) > 2, "llms.txt should have title, description, and sections"

    # Check llms-full.txt exists and has content
    full_content = (site_dir / "llms-full.txt").read_text(encoding="utf-8")
    assert len(full_content) > 0, "llms-full.txt should have content"

    # llms-full.txt should contain actual page content, not just links
    assert "Welcome" in full_content or "Installation" in full_content, (
        "llms-full.txt should contain actual page content"
    )
