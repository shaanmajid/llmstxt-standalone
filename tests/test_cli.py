"""Tests for CLI."""

import shutil
from pathlib import Path

from typer.testing import CliRunner

from llmstxt_standalone.cli import app

runner = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "llms.txt" in result.stdout.lower() or "Generate" in result.stdout


def test_cli_missing_config():
    result = runner.invoke(app, ["--config", "/nonexistent/mkdocs.yml"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "error" in result.output.lower()


def test_cli_missing_site_dir():
    result = runner.invoke(
        app,
        [
            "--config",
            str(FIXTURES / "mkdocs_with_llmstxt.yml"),
            "--site-dir",
            "/nonexistent/site",
        ],
    )
    assert result.exit_code == 1


def test_cli_success(tmp_path: Path):
    # Copy fixtures to tmp_path for output
    shutil.copytree(FIXTURES / "site", tmp_path / "site")

    result = runner.invoke(
        app,
        [
            "--config",
            str(FIXTURES / "mkdocs_with_llmstxt.yml"),
            "--site-dir",
            str(tmp_path / "site"),
            "--output-dir",
            str(tmp_path / "site"),
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "site" / "llms.txt").exists()
    assert (tmp_path / "site" / "llms-full.txt").exists()


def test_cli_dry_run(tmp_path: Path):
    """Test --dry-run flag doesn't write files."""
    shutil.copytree(FIXTURES / "site", tmp_path / "site")
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        [
            "--config",
            str(FIXTURES / "mkdocs_with_llmstxt.yml"),
            "--site-dir",
            str(tmp_path / "site"),
            "--output-dir",
            str(output_dir),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Would generate" in result.output
    # Output directory should not be created in dry-run mode
    assert not output_dir.exists()


def test_cli_quiet(tmp_path: Path):
    """Test --quiet flag suppresses output."""
    shutil.copytree(FIXTURES / "site", tmp_path / "site")

    result = runner.invoke(
        app,
        [
            "--config",
            str(FIXTURES / "mkdocs_with_llmstxt.yml"),
            "--site-dir",
            str(tmp_path / "site"),
            "--output-dir",
            str(tmp_path / "site"),
            "--quiet",
        ],
    )

    assert result.exit_code == 0
    assert result.output.strip() == ""  # No output in quiet mode
    # Files should still be written
    assert (tmp_path / "site" / "llms.txt").exists()


def test_cli_output_dir_separates_output_from_site(tmp_path: Path):
    """Test --output-dir puts ALL output in specified directory, not site-dir."""
    shutil.copytree(FIXTURES / "site", tmp_path / "site")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = runner.invoke(
        app,
        [
            "--config",
            str(FIXTURES / "mkdocs_with_llmstxt.yml"),
            "--site-dir",
            str(tmp_path / "site"),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0

    # All output should be in output_dir
    assert (output_dir / "llms.txt").exists()
    assert (output_dir / "llms-full.txt").exists()
    # Per-page markdown should also be in output_dir
    assert (output_dir / "index.md").exists()

    # site_dir should NOT have the generated files
    # (only the original HTML files should be there)
    assert not (tmp_path / "site" / "llms.txt").exists()
    assert not (tmp_path / "site" / "llms-full.txt").exists()
