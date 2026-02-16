import jinja2
from pathlib import Path
from sqlglot import parse_one, exp


def load_sql(sql_file: Path) -> str:
    """Load and return SQL text from a file path."""
    with open(sql_file, "r", encoding="utf-8") as f:
        return f.read()


def load_sqls(dir_name: Path) -> dict:
    """Load SQL files."""
    sqls = {}

    for f in dir_name.rglob("*.sql"):
        sqls[str(f)] = load_sql(f)

    return sqls


def format_sql(sql: str, context: dict) -> str:
    """Format SQL using jinja templating if necessary."""
    return jinja2.Environment().from_string(sql).render(context)


def _table_name(table: exp.Table) -> str:
    """Extract fully qualified table name from a sqlglot Table expression."""
    parts = []
    if table.catalog:
        parts.append(table.catalog)
    if table.db:
        parts.append(table.db)
    parts.append(table.name)
    return ".".join(parts)


def _parse_insert(tree: exp.Insert) -> dict:
    """Parse an INSERT statement for lineage info."""
    target = _table_name(tree.this.this)

    table_deps = set()
    if tree.expression:
        for table in tree.expression.find_all(exp.Table):
            table_deps.add(_table_name(table))

    # Remove self-references (e.g. target table in a WHERE subquery)
    table_deps.discard(target)

    return {
        "target": target,
        "table_deps": table_deps,
    }


def _parse_merge(tree: exp.Merge) -> dict:
    """Parse a MERGE statement for lineage info."""
    target = _table_name(tree.this)

    table_deps = set()
    using = tree.args.get("using")
    if using:
        for table in using.find_all(exp.Table):
            table_deps.add(_table_name(table))

    table_deps.discard(target)

    return {
        "target": target,
        "table_deps": table_deps,
    }


def get_transaction_type(sql: str) -> dict | None:
    """Parse SQL and return lineage info based on statement type.

    Returns a dict with 'target' (str) and 'table_deps' (set of str),
    or None if the statement type is not yet supported.
    """
    tree = parse_one(sql)

    if isinstance(tree, exp.Insert):
        return _parse_insert(tree)
    if isinstance(tree, exp.Merge):
        return _parse_merge(tree)

    return None
