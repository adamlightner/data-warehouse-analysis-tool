"""Lineage graph building and visualization generation."""

import json
import webbrowser
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


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

    def add_node(self, node: Node) -> None:
        """Add a node to the graph if it doesn't exist."""
        if node.id not in self._node_ids:
            self.nodes.append(node)
            self._node_ids.add(node.id)

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)

    def to_dict(self) -> dict:
        """Convert graph to dictionary for JSON serialization."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges]
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert graph to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def build_graph_from_dags(dags: dict) -> LineageGraph:
    """
    Build a lineage graph from DAG definitions.

    Args:
        dags: Dictionary mapping file paths to parsed YAML DAG definitions.

    Returns:
        LineageGraph containing all nodes and edges.
    """
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

        for task in tasks:
            task_id = task.get("id")
            if not task_id:
                continue

            # Determine node type based on source file or params
            node_type = _infer_node_type(task)

            # Create task node
            task_node = Node(
                id=f"{dag_name}:{task_id}",
                label=task_id,
                type=node_type,
                dag=dag_name,
                operator=task.get("op_type"),
                source_file=task.get("source_file"),
                params=task.get("params")
            )
            graph.add_node(task_node)

            # Add edge from DAG to task
            graph.add_edge(Edge(
                source=f"dag:{dag_name}",
                target=f"{dag_name}:{task_id}"
            ))

            # Add edges for task dependencies
            depends_on = task.get("depends_on", [])
            for dep in depends_on:
                # Skip self-referential dependencies (bug in sample data)
                if dep == task_id:
                    continue
                graph.add_edge(Edge(
                    source=f"{dag_name}:{dep}",
                    target=f"{dag_name}:{task_id}"
                ))

            # Add table nodes from params
            params = task.get("params", {})
            if params:
                _add_table_nodes(graph, dag_name, task_id, params)

    return graph


def _infer_node_type(task: dict) -> str:
    """Infer node type from task definition."""
    source_file = task.get("source_file", "").lower()
    params = task.get("params", {})
    target = params.get("TARGET_TABLE", "").lower() if params else ""

    if "staging" in source_file or "staging" in target or "stg_" in source_file:
        return "staging"
    elif "dimension" in source_file or "dimension" in target or "dim_" in source_file:
        return "dimension"
    elif "fact" in source_file or "fact" in target or "fct_" in source_file:
        return "fact"
    elif task.get("op_type") == "PythonOperator":
        return "task"
    elif "SnowflakeOperator" in task.get("op_type", ""):
        return "table"
    else:
        return "task"


def _add_table_nodes(graph: LineageGraph, dag_name: str, task_id: str, params: dict) -> None:
    """Add table nodes and edges from task parameters."""
    source_table = params.get("SOURCE_TABLE")
    target_table = params.get("TARGET_TABLE")

    if source_table:
        source_type = _infer_table_type(source_table)
        source_node = Node(
            id=f"table:{source_table}",
            label=source_table,
            type=source_type
        )
        graph.add_node(source_node)

        # Edge from source table to task
        graph.add_edge(Edge(
            source=f"table:{source_table}",
            target=f"{dag_name}:{task_id}"
        ))

    if target_table:
        target_type = _infer_table_type(target_table)
        target_node = Node(
            id=f"table:{target_table}",
            label=target_table,
            type=target_type
        )
        graph.add_node(target_node)

        # Edge from task to target table
        graph.add_edge(Edge(
            source=f"{dag_name}:{task_id}",
            target=f"table:{target_table}"
        ))


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


def generate_html(graph: LineageGraph, output_path: Optional[Path] = None) -> str:
    """
    Generate interactive HTML visualization from a lineage graph.

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

    # Replace placeholders
    html = html.replace("/* CSS_PLACEHOLDER */", css)
    html = html.replace("/* GRAPH_DATA_PLACEHOLDER */", graph.to_json())
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
