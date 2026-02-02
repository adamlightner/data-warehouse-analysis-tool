"""CLI entry point for DWAT."""

import click
from pathlib import Path

from dwat.parsers.dag_parser import load_yamls, extract_tasks
from dwat.parsers.query_parser import ParseQuery

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
    # click.echo(dags)
    tasks = extract_tasks(dags)
    click.echo(tasks)


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def parse(path: Path):
    """Parse SQL file."""
    click.echo(type(path))
    ParseQuery(path)


if __name__ == "__main__":
    main()
