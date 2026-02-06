"""CLI entry point for DWAT."""

import click
from pathlib import Path

from dwat.parsers.dag_parser import load_yamls, extract_tasks
from dwat.parsers.query_parser import ParseQuery
from dwat.lineage import generate_html_multi_view, open_in_browser

@click.group()
@click.version_option(version="0.1.0", prog_name="dwat")
def main():
    """DWAT - Data Warehouse Analysis Tool.

    Analyze SQL and YAML files to understand data warehouse logic.
    """
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--recursive", "-r", is_flag=True, help="Recursively scan directories")
def analyze(path: Path, recursive: bool):
    """Analyze SQL and YAML files in the given path."""
    click.echo(f"Analyzing: {path}")
    click.echo(f"Recursive: {recursive}")

    # TODO: Implement analysis logic
    click.echo("Analysis not yet implemented - placeholder for future functionality")

@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def dags(path: Path):
    """Load DAGs from YML files."""
    dags = load_yamls(path)
    click.echo(dags)
    # tasks = extract_tasks(dags)
    # click.echo(tasks)


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def parse(path: Path):
    """Parse SQL file."""
    click.echo(type(path))
    ParseQuery(path)


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default="lineage.html",
              help="Output HTML file path")
@click.option("--open", "open_browser", is_flag=True, help="Open in browser after generating")
def lineage(path: Path, output: Path, open_browser: bool):
    """Generate interactive lineage visualization from DAG definitions."""
    click.echo(f"Loading DAGs from: {path}")
    dags = load_yamls(path)

    if not dags:
        click.echo("No YAML files found.", err=True)
        return

    click.echo(f"Found {len(dags)} DAG file(s)")

    # Generate HTML with all view modes
    generate_html_multi_view(dags, output)
    click.echo(f"Generated: {output}")

    if open_browser:
        open_in_browser(output)
        click.echo("Opened in browser")


if __name__ == "__main__":
    main()
