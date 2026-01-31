"""Command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from llmstxt_standalone import __version__
from llmstxt_standalone.config import load_config
from llmstxt_standalone.generate import generate_llms_txt

app = typer.Typer(
    help="Generate llms.txt from built HTML documentation.",
    no_args_is_help=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"llmstxt-standalone {__version__}")
        raise typer.Exit()


@app.command()
def main(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to mkdocs.yml config file"),
    ] = Path("mkdocs.yml"),
    site_dir: Annotated[
        Path,
        typer.Option("--site-dir", "-s", help="Path to built HTML site directory"),
    ] = Path("site"),
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir", "-o", help="Output directory (defaults to site-dir)"
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Preview what would be generated without writing files",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress output (exit code only)"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed progress"),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version",
        ),
    ] = False,
) -> None:
    """Generate llms.txt and llms-full.txt from built HTML documentation."""
    # Resolve output directory
    out_dir = output_dir or site_dir

    # quiet overrides verbose
    if quiet:
        verbose = False

    def log(msg: str, color: str = "green") -> None:
        if not quiet:
            typer.secho(msg, fg=color)

    # Validate inputs
    if not config.exists():
        typer.secho(f"Error: Config file not found: {config}", fg="red", err=True)
        raise typer.Exit(1)

    if not site_dir.exists():
        typer.secho(f"Error: Site directory not found: {site_dir}", fg="red", err=True)
        typer.secho(
            "Hint: Run 'mkdocs build' first to generate the HTML documentation.",
            fg="yellow",
            err=True,
        )
        raise typer.Exit(1)

    # Load config
    try:
        cfg = load_config(config)
    except Exception as e:
        typer.secho(f"Error loading config: {e}", fg="red", err=True)
        raise typer.Exit(1) from None

    if verbose and not quiet:
        typer.echo(f"Site: {cfg.site_name}")
        typer.echo(f"Sections: {list(cfg.sections.keys())}")
        if dry_run:
            typer.echo("Dry run - no files will be written")

    # Generate content
    result = generate_llms_txt(
        config=cfg,
        site_dir=site_dir,
        output_dir=out_dir,
        verbose=verbose,
        dry_run=dry_run,
        warn_on_empty=not quiet,
    )

    # Define output paths
    llms_path = out_dir / "llms.txt"
    full_path = out_dir / cfg.full_output

    # Write output files (skip in dry-run mode)
    if dry_run:
        action = "Would generate"
        color = "yellow"
    else:
        action = "Generated"
        color = "green"
        out_dir.mkdir(parents=True, exist_ok=True)
        llms_path.write_text(result.llms_txt, encoding="utf-8")
        full_path.write_text(result.llms_full_txt, encoding="utf-8")

    log(f"{action} {llms_path} ({len(result.llms_txt):,} bytes)", color)
    log(f"{action} {full_path} ({len(result.llms_full_txt):,} bytes)", color)
    log(f"{action} {len(result.markdown_files)} markdown files", color)


if __name__ == "__main__":
    app()
