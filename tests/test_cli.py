"""Tests for CLI."""

from pathlib import Path

from typer.testing import CliRunner

from llmstxt_gen.cli import app

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
    result = runner.invoke(app, [
        "--config", str(FIXTURES / "mkdocs_with_llmstxt.yml"),
        "--site-dir", "/nonexistent/site",
    ])
    assert result.exit_code == 1


def test_cli_success(tmp_path: Path):
    # Copy fixtures to tmp_path for output
    import shutil
    shutil.copytree(FIXTURES / "site", tmp_path / "site")

    result = runner.invoke(app, [
        "--config", str(FIXTURES / "mkdocs_with_llmstxt.yml"),
        "--site-dir", str(tmp_path / "site"),
        "--output-dir", str(tmp_path / "site"),
    ])

    assert result.exit_code == 0
    assert (tmp_path / "site" / "llms.txt").exists()
    assert (tmp_path / "site" / "llms-full.txt").exists()
