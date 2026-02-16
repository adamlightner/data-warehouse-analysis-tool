"""Lineage graph building and visualization generation."""

import json
import webbrowser
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from dwat.parsers.sql_parser import load_sql, format_sql, get_transaction_type


@dataclass
class Node:
    """Represents a node in the lineage graph."""
    id: str
    label: str
    type: str = "default"
    dag: Optional[str] = None
    operator: Optional[str] = None
    source_file: Optional[str] = None
    params: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Edge:
    """Represents an edge (dependency) in the lineage graph."""
    source: str
    target: str
    label: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LineageGraph:
    """Graph structure for lineage visualization."""
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    _node_ids: set = field(default_factory=set, repr=False)
    _edge_keys: set = field(default_factory=set, repr=False)

    def add_node(self, node: Node) -> None:
        """Add a node to the graph if it doesn't exist."""
        if node.id not in self._node_ids:
            self.nodes.append(node)
            self._node_ids.add(node.id)

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph if it doesn't exist."""
        key = (edge.source, edge.target)
        if key not in self._edge_keys:
            self.edges.append(edge)
            self._edge_keys.add(key)

    def to_dict(self) -> dict:
        """Convert graph to dictionary for JSON serialization."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges]
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert graph to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def build_graph_from_dags(dags: dict, view_mode: str = "dag") -> LineageGraph:
    """
    Build a lineage graph from DAG definitions.

    Args:
        dags: Dictionary mapping file paths to parsed YAML DAG definitions.
        view_mode: "dag" for DAG/task view, "table" for table lineage view.

    Returns:
        LineageGraph containing all nodes and edges.
    """
    if view_mode == "dag":
        return _build_dag_view(dags)
    else:
        return _build_table_view(dags)


def _build_dag_view(dags: dict) -> LineageGraph:
    """Build DAG-centric view: DAGs -> Tasks (colored by operator type)."""
    graph = LineageGraph()

    for dag_file, dag_obj in dags.items():
        if not dag_obj:
            continue

        dag_name = list(dag_obj.keys())[0]
        dag_def = dag_obj[dag_name]

        # Add DAG as a node
        dag_node = Node(
            id=f"dag:{dag_name}",
            label=dag_name,
            type="dag",
            source_file=dag_file
        )
        graph.add_node(dag_node)

        # Process tasks
        tasks = dag_def.get("tasks", [])
        if not tasks:
            continue

        # Collect task edges first for transitive reduction
        task_edges = []

        for task in tasks:
            task_id = task.get("id")
            if not task_id:
                continue

            # Use op_type as the node type for coloring
            op_type = task.get("op_type", "task")

            # Create task node
            task_node = Node(
                id=f"{dag_name}:{task_id}",
                label=task_id,
                type=op_type,
                dag=dag_name,
                operator=op_type,
                source_file=task.get("source_file"),
                params=task.get("params")
            )
            graph.add_node(task_node)

            # Add edge from DAG to first task (tasks with no dependencies)
            depends_on = task.get("depends_on", [])
            if not depends_on:
                graph.add_edge(Edge(
                    source=f"dag:{dag_name}",
                    target=f"{dag_name}:{task_id}"
                ))

            # Collect task dependency edges
            for dep in depends_on:
                if dep == task_id:
                    continue
                task_edges.append((dep, task_id))

        # Transitive reduction: remove edges implied by longer paths
        reduced = _transitive_reduce(task_edges)
        for source, target in reduced:
            graph.add_edge(Edge(
                source=f"{dag_name}:{source}",
                target=f"{dag_name}:{target}"
            ))

    return graph


def _transitive_reduce(edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Remove edges that are implied by transitive paths."""
    # Build adjacency list
    children = {}
    for src, tgt in edges:
        children.setdefault(src, set()).add(tgt)

    def can_reach(start: str, end: str, excluded_edge: tuple[str, str]) -> bool:
        """Check if end is reachable from start without using the excluded edge."""
        visited = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node == end:
                return True
            if node in visited:
                continue
            visited.add(node)
            for child in children.get(node, []):
                if (node, child) == excluded_edge:
                    continue
                stack.append(child)
        return False

    return [
        (src, tgt) for src, tgt in edges
        if not can_reach(src, tgt, (src, tgt))
    ]


def _build_table_view(dags: dict) -> LineageGraph:
    """Build table-centric view by parsing SQL files for lineage.

    For each task with a source_file and params, loads the SQL file,
    renders Jinja templates with params, then parses with sqlglot to
    extract the target table and its dependencies.
    """
    graph = LineageGraph()

    for dag_file, dag_obj in dags.items():
        if not dag_obj:
            continue

        dag_name = list(dag_obj.keys())[0]
        dag_def = dag_obj[dag_name]

        tasks = dag_def.get("tasks", [])
        if not tasks:
            continue

        for task in tasks:
            source_file = task.get("source_file")
            params = task.get("params", {})

            if not source_file or not params:
                continue

            # Resolve SQL file path (relative to CWD, then relative to YAML dir)
            sql_path = Path(source_file)
            if not sql_path.is_absolute():
                sql_path = Path.cwd() / source_file
            if not sql_path.exists():
                sql_path = Path(dag_file).parent / source_file
            if not sql_path.exists():
                continue

            # Load SQL, render Jinja with params, parse for lineage
            try:
                raw_sql = load_sql(sql_path)
                formatted_sql = format_sql(raw_sql, params)
                result = get_transaction_type(formatted_sql)
            except Exception:
                continue

            if not result:
                continue

            target = result["target"]
            deps = result.get("table_deps", set())

            # Add target table node
            target_type = _infer_table_type(target)
            graph.add_node(Node(
                id=f"table:{target}",
                label=target,
                type=target_type
            ))

            # Add dependency nodes and edges
            for dep in deps:
                dep_type = _infer_table_type(dep)
                graph.add_node(Node(
                    id=f"table:{dep}",
                    label=dep,
                    type=dep_type
                ))
                graph.add_edge(Edge(
                    source=f"table:{dep}",
                    target=f"table:{target}"
                ))

    return graph


def _infer_table_type(table_name: str) -> str:
    """Infer table type from table name."""
    name_lower = table_name.lower()

    if "staging" in name_lower or name_lower.startswith("stg"):
        return "staging"
    elif "dimension" in name_lower or name_lower.startswith("dim"):
        return "dimension"
    elif "fact" in name_lower or name_lower.startswith("fct"):
        return "fact"
    elif "ingestion" in name_lower or "raw" in name_lower:
        return "source"
    else:
        return "table"


def generate_html_multi_view(dags: dict, output_path: Optional[Path] = None) -> str:
    """
    Generate interactive HTML visualization with multiple view modes.

    Args:
        dags: Raw DAG definitions dictionary.
        output_path: Optional path to write the HTML file.

    Returns:
        The generated HTML string.
    """
    # Build graphs for each view mode
    dag_graph = build_graph_from_dags(dags, view_mode="dag")
    table_graph = build_graph_from_dags(dags, view_mode="table")

    # Combine into multi-view data structure
    all_graphs = {
        "dag": dag_graph.to_dict(),
        "table": table_graph.to_dict(),
        "metric": {"nodes": [], "edges": []}
    }

    # Load template files
    ui_dir = Path(__file__).parent / "ui"
    template_path = ui_dir / "template.html"
    styles_path = ui_dir / "styles.css"
    js_path = ui_dir / "visualization.js"

    with open(template_path) as f:
        html = f.read()

    with open(styles_path) as f:
        css = f.read()

    with open(js_path) as f:
        js = f.read()

    # Replace placeholders
    html = html.replace("/* CSS_PLACEHOLDER */", css)
    html = html.replace("/* GRAPH_DATA_PLACEHOLDER */", json.dumps(all_graphs, indent=2))
    html = html.replace("/* JS_PLACEHOLDER */", js)

    # Write to file if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html)

    return html


def generate_html(graph: LineageGraph, output_path: Optional[Path] = None) -> str:
    """
    Generate interactive HTML visualization from a lineage graph.

    DEPRECATED: Use generate_html_multi_view for new code.

    Args:
        graph: The LineageGraph to visualize.
        output_path: Optional path to write the HTML file.

    Returns:
        The generated HTML string.
    """
    # Load template files
    ui_dir = Path(__file__).parent / "ui"
    template_path = ui_dir / "template.html"
    styles_path = ui_dir / "styles.css"
    js_path = ui_dir / "visualization.js"

    with open(template_path) as f:
        html = f.read()

    with open(styles_path) as f:
        css = f.read()

    with open(js_path) as f:
        js = f.read()

    # Wrap single graph in multi-view format for compatibility
    all_graphs = {
        "dag": graph.to_dict(),
        "table": graph.to_dict(),
        "metric": graph.to_dict()
    }

    # Replace placeholders
    html = html.replace("/* CSS_PLACEHOLDER */", css)
    html = html.replace("/* GRAPH_DATA_PLACEHOLDER */", json.dumps(all_graphs, indent=2))
    html = html.replace("/* JS_PLACEHOLDER */", js)

    # Write to file if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html)

    return html


def open_in_browser(html_path: Path) -> None:
    """Open the generated HTML file in the default browser."""
    webbrowser.open(f"file://{html_path.absolute()}")
