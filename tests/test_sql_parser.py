"""Tests for the SQL parser module."""

from pathlib import Path

from dwat.parsers.sql_parser import (
    load_sql,
    load_sqls,
    format_sql,
    get_transaction_type,
)


SQL_DIR = Path(__file__).parent.parent / "examples" / "sql"


# ---- load / format ----

def test_load_sql():
    sql = load_sql(SQL_DIR / "staging" / "stg_game.sql")
    assert isinstance(sql, str)
    assert "insert into" in sql.lower()


def test_load_sqls():
    sqls = load_sqls(SQL_DIR)
    assert len(sqls) == 3
    for path, content in sqls.items():
        assert content.strip()


def test_format_sql_renders_jinja():
    raw = "select * from {{ TABLE }}"
    result = format_sql(raw, {"TABLE": "MY_SCHEMA.MY_TABLE"})
    assert result == "select * from MY_SCHEMA.MY_TABLE"


def test_format_sql_no_jinja_passthrough():
    raw = "select 1"
    assert format_sql(raw, {}) == "select 1"


# ---- INSERT parsing ----

def test_parse_insert_staging():
    raw = load_sql(SQL_DIR / "staging" / "stg_game.sql")
    formatted = format_sql(raw, {
        "TARGET_TABLE": "STAGING.NFL_GAME",
        "SOURCE_TABLE": "INGESTION.NFL_GAME",
    })
    result = get_transaction_type(formatted)

    assert result is not None
    assert result["target"] == "STAGING.NFL_GAME"
    assert "INGESTION.NFL_GAME" in result["table_deps"]
    # Target should not appear in its own deps
    assert "STAGING.NFL_GAME" not in result["table_deps"]


def test_parse_insert_fact_with_joins():
    raw = load_sql(SQL_DIR / "fact" / "fct_game.sql")
    formatted = format_sql(raw, {
        "TARGET_TABLE": "FACT.NFL_GAME",
        "SOURCE_TABLE": "STAGING.NFL_GAME",
        "TEAM_TABLE": "DIMENSION.NFL_TEAM",
    })
    result = get_transaction_type(formatted)

    assert result is not None
    assert result["target"] == "FACT.NFL_GAME"
    assert "STAGING.NFL_GAME" in result["table_deps"]
    assert "DIMENSION.NFL_TEAM" in result["table_deps"]
    # Self-reference in WHERE subquery should be filtered out
    assert "FACT.NFL_GAME" not in result["table_deps"]


# ---- MERGE parsing ----

def test_parse_merge():
    raw = load_sql(SQL_DIR / "dimension" / "dim_team.sql")
    formatted = format_sql(raw, {
        "TARGET_TABLE": "DIMENSION.NFL_TEAM",
        "SOURCE_TABLE": "INGESTION.NFL_TEAM",
    })
    result = get_transaction_type(formatted)

    assert result is not None
    assert result["target"] == "DIMENSION.NFL_TEAM"
    assert "INGESTION.NFL_TEAM" in result["table_deps"]
    assert "DIMENSION.NFL_TEAM" not in result["table_deps"]


# ---- Unsupported / edge cases ----

def test_unsupported_statement_returns_none():
    result = get_transaction_type("SELECT 1")
    assert result is None


def test_insert_no_self_reference():
    sql = "INSERT INTO A.B (col) SELECT col FROM C.D"
    result = get_transaction_type(sql)
    assert result["target"] == "A.B"
    assert result["table_deps"] == {"C.D"}
