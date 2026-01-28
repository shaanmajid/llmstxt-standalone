"""Command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from llmstxt_gen import __version__
from llmstxt_gen.config import load_config
from llmstxt_gen.generate import generate_llms_txt

app = typer.Typer(
    help="Generate llms.txt from built HTML documentation.",
    no_args_is_help=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"llmstxt-gen {__version__}")
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

    # Validate inputs
    if not config.exists():
        typer.echo(f"Error: Config file not found: {config}", err=True)
        raise typer.Exit(1)

    if not site_dir.exists():
        typer.echo(f"Error: Site directory not found: {site_dir}", err=True)
        typer.echo(
            "Hint: Run 'mkdocs build' first to generate the HTML documentation.",
            err=True,
        )
        raise typer.Exit(1)

    # Load config
    try:
        cfg = load_config(config)
    except Exception as e:
        typer.echo(f"Error loading config: {e}", err=True)
        raise typer.Exit(1) from None

    if verbose:
        typer.echo(f"Site: {cfg.site_name}")
        typer.echo(f"Sections: {list(cfg.sections.keys())}")

    # Generate content
    llms_txt, llms_full_txt = generate_llms_txt(
        config=cfg,
        site_dir=site_dir,
        verbose=verbose,
    )

    # Write output files
    out_dir.mkdir(parents=True, exist_ok=True)

    llms_path = out_dir / "llms.txt"
    llms_path.write_text(llms_txt, encoding="utf-8")

    full_path = out_dir / cfg.full_output
    full_path.write_text(llms_full_txt, encoding="utf-8")

    typer.echo(f"Generated {llms_path} ({len(llms_txt):,} bytes)")
    typer.echo(f"Generated {full_path} ({len(llms_full_txt):,} bytes)")


if __name__ == "__main__":
    app()
