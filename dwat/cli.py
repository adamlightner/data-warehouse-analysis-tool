"""CLI entry point for DWAT."""

import click
import json
from pathlib import Path

from dwat.parsers.dag_parser import load_dag, load_dags, extract_tasks
from dwat.parsers.sql_parser import load_sql, load_sqls, format_sql
from dwat.lineage import generate_html_multi_view, open_in_browser

@click.group()
@click.version_option(version="0.1.0", prog_name="dwat")
def main():
    """DWAT - Data Warehouse Analysis Tool.

    Analyze SQL and YAML files to understand data warehouse logic.
    """
    pass

# -------------------------------
# COMMAND: Analyze
# -------------------------------

# @main.command()
# @click.argument("path", type=click.Path(exists=True, path_type=Path))
# @click.option("--recursive", "-r", is_flag=True, help="Recursively scan directories")
# def analyze(path: Path, recursive: bool):
#     """Analyze SQL and YAML files in the given path."""
#     click.echo(f"Analyzing: {path}")
#     click.echo(f"Recursive: {recursive}")

#     # TODO: Implement analysis logic
#     click.echo("Analysis not yet implemented - placeholder for future functionality")

# -------------------------------
# COMMAND: Parse
# -------------------------------

@main.group()
def parse() -> None:
    """Parse SQL and DAG files."""

@parse.command("sql")
@click.argument("file_name", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--context", default="{}", show_default=True, help="Params for jinja templating")
@click.option("--verbose", is_flag=True, help="Print SQL")
def parse_sql(file_name: Path, context: str, verbose: bool) -> None:
    """Load SQL file"""
    ctx = json.loads(context)
    query = load_sql(file_name)
    f_query = format_sql(query, ctx)

    if verbose:
        click.echo(f_query)

@parse.command("sqls")
@click.argument("dir_name", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--verbose", is_flag=True, help="Print SQL")
def parse_sqls(dir_name: Path, verbose: bool) -> None:
    """Load SQL file"""
    sqls = load_sqls(dir_name)

    if verbose:
        click.echo(sqls)

@parse.command("dag")
@click.argument("file_name", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--verbose", is_flag=True, help="Print SQL")
def parse_dag(file_name: Path, verbose: bool) -> None:
    """Load SQL file"""
    
    dag = load_dag(file_name)

    if verbose:
        click.echo(dag)

@parse.command("dags")
@click.argument("dir_name", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--verbose", is_flag=True, help="Print SQL")
def parse_dags(dir_name: Path, verbose: bool) -> None:
    """Load SQL file"""
    dags = load_dags(dir_name)

    if verbose:
        click.echo(dags)

# -------------------------------
# COMMAND: Lineage
# -------------------------------

@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default="lineage.html", help="Output HTML file path")
@click.option("--open", "open_browser", is_flag=True, help="Open in browser after generating")
def lineage(path: Path, output: Path, open_browser: bool):
    """Generate interactive lineage visualization from DAG definitions."""
    click.echo(f"Loading DAGs from: {path}")
    dags = load_dags(path)

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
