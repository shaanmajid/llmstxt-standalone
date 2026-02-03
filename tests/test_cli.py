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
    assert "build" in result.stdout
    assert "init" in result.stdout
    assert "validate" in result.stdout


def test_cli_no_args_shows_help():
    result = runner.invoke(app, [])
    # Exit code 2 is standard for "no command specified" (usage error)
    assert result.exit_code == 2
    assert "build" in result.stdout
    assert "init" in result.stdout
    assert "validate" in result.stdout


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "llmstxt-standalone" in result.stdout


def test_build_help():
    result = runner.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "llms.txt" in result.stdout.lower() or "Generate" in result.stdout


def test_build_missing_config():
    result = runner.invoke(app, ["build", "--config", "/nonexistent/mkdocs.yml"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "error" in result.output.lower()


def test_build_missing_site_dir():
    result = runner.invoke(
        app,
        [
            "build",
            "--config",
            str(FIXTURES / "mkdocs_with_llmstxt.yml"),
            "--site-dir",
            "/nonexistent/site",
        ],
    )
    assert result.exit_code == 1


def test_build_success(tmp_path: Path):
    # Copy fixtures to tmp_path for output
    shutil.copytree(FIXTURES / "site", tmp_path / "site")

    result = runner.invoke(
        app,
        [
            "build",
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


def test_build_dry_run(tmp_path: Path):
    """Test --dry-run flag doesn't write files."""
    shutil.copytree(FIXTURES / "site", tmp_path / "site")
    output_dir = tmp_path / "output"

    result = runner.invoke(
        app,
        [
            "build",
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


def test_build_quiet(tmp_path: Path):
    """Test --quiet flag suppresses output."""
    shutil.copytree(FIXTURES / "site", tmp_path / "site")

    result = runner.invoke(
        app,
        [
            "build",
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


def test_build_quiet_failure():
    """Test --quiet suppresses error output on failure."""
    result = runner.invoke(
        app, ["build", "--config", "/nonexistent/mkdocs.yml", "--quiet"]
    )

    assert result.exit_code == 1
    assert result.output.strip() == ""


def test_build_output_dir_separates_output_from_site(tmp_path: Path):
    """Test --output-dir puts ALL output in specified directory, not site-dir."""
    shutil.copytree(FIXTURES / "site", tmp_path / "site")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = runner.invoke(
        app,
        [
            "build",
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


def test_build_no_sections_configured(tmp_path: Path):
    """Test CLI errors when no sections are configured (no nav, no explicit sections)."""
    shutil.copytree(FIXTURES / "site", tmp_path / "site")

    result = runner.invoke(
        app,
        [
            "build",
            "--config",
            str(FIXTURES / "mkdocs_no_nav.yml"),
            "--site-dir",
            str(tmp_path / "site"),
        ],
    )

    assert result.exit_code == 1
    assert "No sections configured" in result.output
    assert "nav" in result.output.lower()


def test_build_rejects_full_output_path_traversal(tmp_path: Path):
    """Test build rejects full_output paths that escape output_dir."""
    shutil.copytree(FIXTURES / "site", tmp_path / "site")

    config_path = tmp_path / "mkdocs.yml"
    base_config = (FIXTURES / "mkdocs_with_llmstxt.yml").read_text(encoding="utf-8")
    config_path.write_text(
        base_config.replace("full_output: llms-full.txt", "full_output: ../escape.txt"),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "build",
            "--config",
            str(config_path),
            "--site-dir",
            str(tmp_path / "site"),
        ],
    )

    assert result.exit_code == 1
    assert "full_output" in result.output.lower()


def test_build_rejects_absolute_full_output(tmp_path: Path):
    """Test build rejects absolute full_output paths."""
    shutil.copytree(FIXTURES / "site", tmp_path / "site")

    config_path = tmp_path / "mkdocs.yml"
    base_config = (FIXTURES / "mkdocs_with_llmstxt.yml").read_text(encoding="utf-8")
    config_path.write_text(
        base_config.replace(
            "full_output: llms-full.txt", "full_output: /tmp/escape.txt"
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "build",
            "--config",
            str(config_path),
            "--site-dir",
            str(tmp_path / "site"),
        ],
    )

    assert result.exit_code == 1
    assert "full_output" in result.output.lower()


# Tests for init subcommand


def test_init_missing_config():
    """Test init errors when config file doesn't exist."""
    result = runner.invoke(app, ["init", "--config", "/nonexistent/mkdocs.yml"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


def test_init_creates_plugin_entry(tmp_path: Path):
    """Test init adds llmstxt plugin to mkdocs.yml."""
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Test\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config)])

    assert result.exit_code == 0
    assert "Added llmstxt plugin" in result.output

    content = config.read_text(encoding="utf-8")
    assert "plugins:" in content
    assert "llmstxt" in content


def test_init_adds_to_existing_plugins(tmp_path: Path):
    """Test init adds llmstxt to existing plugins list."""
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Test\nplugins:\n  - search\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config)])

    assert result.exit_code == 0

    content = config.read_text(encoding="utf-8")
    assert "search" in content
    assert "llmstxt" in content


def test_init_handles_null_plugins(tmp_path: Path):
    """Test init handles plugins: null by initializing a list."""
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Test\nplugins:\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config)])

    assert result.exit_code == 0
    content = config.read_text(encoding="utf-8")
    assert "plugins:" in content
    assert "llmstxt" in content


def test_init_errors_if_llmstxt_exists(tmp_path: Path):
    """Test init errors if llmstxt plugin already configured."""
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Test\nplugins:\n  - llmstxt\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config)])

    assert result.exit_code == 1
    assert "already configured" in result.output


def test_init_force_overwrites(tmp_path: Path):
    """Test init --force overwrites existing llmstxt plugin."""
    config = tmp_path / "mkdocs.yml"
    config.write_text(
        "site_name: Test\nplugins:\n  - llmstxt:\n      sections:\n        Old: [old.md]\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["init", "--config", str(config), "--force"])

    assert result.exit_code == 0
    assert "Added llmstxt plugin" in result.output


def test_init_includes_commented_example(tmp_path: Path):
    """Test init adds commented example configuration."""
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Test\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config)])

    assert result.exit_code == 0

    content = config.read_text(encoding="utf-8")
    assert "# markdown_description" in content or "llmstxt" in content


def test_init_quiet_success(tmp_path: Path):
    """Test init --quiet suppresses output on success."""
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Test\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config), "--quiet"])

    assert result.exit_code == 0
    assert result.output.strip() == ""
    # Config should still be modified
    content = config.read_text(encoding="utf-8")
    assert "llmstxt" in content


def test_init_quiet_failure():
    """Test init --quiet suppresses error output on failure."""
    result = runner.invoke(
        app, ["init", "--config", "/nonexistent/mkdocs.yml", "--quiet"]
    )

    assert result.exit_code == 1
    assert result.output.strip() == ""


def test_init_verbose(tmp_path: Path):
    """Test init --verbose shows extra details."""
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Test\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config), "--verbose"])

    assert result.exit_code == 0
    assert "Added llmstxt plugin" in result.output
    # Verbose should show what was added
    assert "llmstxt" in result.output


def test_init_quiet_force(tmp_path: Path):
    """Test init --quiet --force works correctly together."""
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Test\nplugins:\n  - llmstxt\n", encoding="utf-8")

    result = runner.invoke(app, ["init", "--config", str(config), "--quiet", "--force"])

    assert result.exit_code == 0
    assert result.output.strip() == ""
    content = config.read_text(encoding="utf-8")
    assert "llmstxt" in content


# Tests for validate subcommand


def test_validate_valid_config():
    """Test validate succeeds with valid config."""
    result = runner.invoke(
        app, ["validate", "--config", str(FIXTURES / "mkdocs_with_llmstxt.yml")]
    )

    assert result.exit_code == 0
    assert "Config valid" in result.output
    assert "Site:" in result.output
    assert "Sections:" in result.output
    assert "Pages:" in result.output


def test_validate_missing_config():
    """Test validate errors when config file doesn't exist."""
    result = runner.invoke(app, ["validate", "--config", "/nonexistent/mkdocs.yml"])

    assert result.exit_code == 1
    assert "Config invalid" in result.output
    assert "not found" in result.output.lower()


def test_validate_invalid_config(tmp_path: Path):
    """Test validate errors with invalid config."""
    config = tmp_path / "mkdocs.yml"
    config.write_text(
        "site_name: Test\nplugins:\n  - llmstxt:\n      sections: invalid\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "--config", str(config)])

    assert result.exit_code == 1
    assert "Config invalid" in result.output


def test_validate_malformed_yaml(tmp_path: Path):
    """Test validate errors with malformed YAML syntax."""
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Test\n  bad_indent: value\n", encoding="utf-8")

    result = runner.invoke(app, ["validate", "--config", str(config)])

    assert result.exit_code == 1
    assert "Config invalid" in result.output


def test_validate_quiet_success():
    """Test validate --quiet has no output on success."""
    result = runner.invoke(
        app,
        ["validate", "--config", str(FIXTURES / "mkdocs_with_llmstxt.yml"), "--quiet"],
    )

    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_validate_quiet_failure(tmp_path: Path):
    """Test validate --quiet has no output on failure (just exit code)."""
    result = runner.invoke(
        app, ["validate", "--config", "/nonexistent/mkdocs.yml", "--quiet"]
    )

    assert result.exit_code == 1
    assert result.output.strip() == ""


def test_validate_verbose():
    """Test validate --verbose shows extra config details."""
    result = runner.invoke(
        app,
        [
            "validate",
            "--config",
            str(FIXTURES / "mkdocs_with_llmstxt.yml"),
            "--verbose",
        ],
    )

    assert result.exit_code == 0
    assert "Config valid" in result.output
    # Verbose should show section names
    assert "Getting Started" in result.output
