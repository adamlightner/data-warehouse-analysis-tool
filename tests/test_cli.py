"""Tests for the CLI module."""

from pathlib import Path

from click.testing import CliRunner

from dwat.cli import main


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
DEFINITIONS_DIR = EXAMPLES_DIR / "definitions"
SQL_DIR = EXAMPLES_DIR / "sql"


runner = CliRunner()


# ---- top-level ----

def test_help():
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "DWAT" in result.output


def test_version():
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


# ---- parse dag(s) ----

def test_parse_dag():
    result = runner.invoke(main, ["parse", "dag", str(DEFINITIONS_DIR / "games.yml")])
    assert result.exit_code == 0


def test_parse_dags():
    result = runner.invoke(main, ["parse", "dags", str(DEFINITIONS_DIR)])
    assert result.exit_code == 0


# ---- parse sql(s) ----

def test_parse_sql():
    result = runner.invoke(main, ["parse", "sql", str(SQL_DIR / "staging" / "stg_game.sql")])
    assert result.exit_code == 0


def test_parse_sql_verbose():
    result = runner.invoke(main, [
        "parse", "sql",
        str(SQL_DIR / "staging" / "stg_game.sql"),
        "--context", '{"TARGET_TABLE": "T", "SOURCE_TABLE": "S"}',
        "--verbose",
    ])
    assert result.exit_code == 0
    assert "insert into" in result.output.lower()


def test_parse_sqls():
    result = runner.invoke(main, ["parse", "sqls", str(SQL_DIR)])
    assert result.exit_code == 0


# ---- lineage ----

def test_lineage_generates_html(tmp_path):
    out = tmp_path / "test_lineage.html"
    result = runner.invoke(main, ["lineage", str(DEFINITIONS_DIR), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text()
    assert "DWAT" in content
    assert "graph-data" in content


def test_lineage_no_yaml(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    result = runner.invoke(main, ["lineage", str(empty_dir)])
    assert "No YAML files found" in result.output
