import jinja2
from pathlib import Path

def load_sql(sql_file: Path) -> str:
    """Load and return SQL test from a file path."""
    with open(sql_file, "r", encoding="utf-8") as f:
        return f.read()
    
def load_sqls(dir_name: Path) -> dict:
    """Load SQL files."""
    sqls = {}

    for f in dir_name.rglob("*.sql"):
        sqls[str(f)] = load_sql(f)

    return sqls
    
def format_sql(sql: str, context: dict) -> str:
    """Format SQL using jinja templating if necessary"""
    return jinja2.Environment().from_string(sql).render(context)
