# DWAT - Data Warehouse Analysis Tool

A Python tool to analyze SQL and YAML files for data warehouse logic, providing insights into structure, dependencies, and patterns.

## Setup

### Prerequisites
- Python 3.11+ (tested with 3.12)
- pip

### Installation

1. Clone or navigate to the project directory

2. Create and activate virtual environment:
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the project in editable mode:
```bash
pip install -e .
```

4. Verify installation:
```bash
dwat --help
```

## Architecture

### Project Structure
```
dwat/
├── dwat/
│   ├── parsers/
│   │   ├── dag_parser.py    # YAML parsing: files → dict
│   │   └── query_parser.py  # SQL parsing (placeholder)
│   ├── lineage.py           # Graph building + HTML generation
│   ├── ui/                  # Visualization templates
│   │   ├── template.html
│   │   ├── styles.css
│   │   └── visualization.js
│   ├── analyzers/           # Analysis logic (future)
│   └── cli.py               # CLI entry point
├── examples/
│   ├── definitions/         # Sample YAML DAG files
│   └── sql_scripts/         # Sample SQL files
├── tests/
└── pyproject.toml
```

### Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   YAML Files    │ ──▶ │   dag_parser     │ ──▶ │   lineage.py    │ ──▶ │  HTML Output    │
│  (DAG defs)     │     │  load_yamls()    │     │ build_graph()   │     │ (interactive)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
                              │                        │
                              ▼                        ▼
                         dict[path, yaml]         LineageGraph
```

---

## Workflow Step-by-Step

### Step 1: YAML Input (DAG Definitions)

**Input:** YAML files defining DAGs with tasks and dependencies

**File:** `examples/definitions/games.yml`

```yaml
load_games:
  catchup: false
  owner: airflow
  schedule: 0 0 1 9 *
  max_active_runs: 1
  max_retries: 2
  tasks:

    - id: get_batch
      op_type: PythonOperator
      source_file: utils/get_batch.py

    - id: insert_to_staging
      op_type: SnowflakeOperator
      pool: nfl
      source_file: sql_scripts/staging/stg_game.sql
      params:
        TARGET_TABLE: STAGING.NFL_GAME
        SOURCE_TABLE: INGESTION.NFL_GAME
      depends_on:
        - get_batch

    - id: insert_to_fact
      op_type: SnowflakeOperator
      pool: nfl
      source_file: sql_scripts/fact/fct_game.sql
      params:
        TARGET_TABLE: FACT.NFL_GAME
        SOURCE_TABLE: STAGING.NFL_GAME
      depends_on:
        - insert_to_staging
```

**Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `<dag_name>` | object | Top-level key is the DAG name |
| `catchup` | bool | Airflow catchup setting |
| `owner` | string | DAG owner |
| `schedule` | string | Cron schedule |
| `tasks` | list | List of task definitions |
| `tasks[].id` | string | Unique task identifier |
| `tasks[].op_type` | string | Operator type (e.g., PythonOperator, SnowflakeOperator) |
| `tasks[].source_file` | string | Path to source file (SQL or Python) |
| `tasks[].params` | object | Key-value parameters (e.g., SOURCE_TABLE, TARGET_TABLE) |
| `tasks[].depends_on` | list | List of upstream task IDs |

---

### Step 2: DAG Parser Output

**Function:** `dag_parser.load_yamls(path: Path) -> dict`

**Output:** Dictionary mapping file paths to parsed YAML content

```python
{
    "examples/definitions/games.yml": {
        "load_games": {
            "catchup": False,
            "owner": "airflow",
            "schedule": "0 0 1 9 *",
            "max_active_runs": 1,
            "max_retries": 2,
            "tasks": [
                {
                    "id": "get_batch",
                    "op_type": "PythonOperator",
                    "source_file": "utils/get_batch.py"
                },
                {
                    "id": "insert_to_staging",
                    "op_type": "SnowflakeOperator",
                    "pool": "nfl",
                    "source_file": "sql_scripts/staging/stg_game.sql",
                    "params": {
                        "TARGET_TABLE": "STAGING.NFL_GAME",
                        "SOURCE_TABLE": "INGESTION.NFL_GAME"
                    },
                    "depends_on": ["get_batch"]
                },
                {
                    "id": "insert_to_fact",
                    "op_type": "SnowflakeOperator",
                    "pool": "nfl",
                    "source_file": "sql_scripts/fact/fct_game.sql",
                    "params": {
                        "TARGET_TABLE": "FACT.NFL_GAME",
                        "SOURCE_TABLE": "STAGING.NFL_GAME"
                    },
                    "depends_on": ["insert_to_staging"]
                }
            ]
        }
    },
    "examples/definitions/teams.yml": {
        "load_teams": {
            # ... similar structure
        }
    }
}
```

---

### Step 3: Lineage Graph Building

**Function:** `lineage.build_graph_from_dags(dags: dict) -> LineageGraph`

**Output:** `LineageGraph` object containing nodes and edges

```python
LineageGraph(
    nodes=[
        Node(id="dag:load_games", label="load_games", type="dag"),
        Node(id="load_games:get_batch", label="get_batch", type="task",
             dag="load_games", operator="PythonOperator"),
        Node(id="load_games:insert_to_staging", label="insert_to_staging", type="staging",
             dag="load_games", operator="SnowflakeOperator",
             params={"TARGET_TABLE": "STAGING.NFL_GAME", "SOURCE_TABLE": "INGESTION.NFL_GAME"}),
        Node(id="table:INGESTION.NFL_GAME", label="INGESTION.NFL_GAME", type="source"),
        Node(id="table:STAGING.NFL_GAME", label="STAGING.NFL_GAME", type="staging"),
        Node(id="table:FACT.NFL_GAME", label="FACT.NFL_GAME", type="fact"),
        # ... more nodes
    ],
    edges=[
        Edge(source="dag:load_games", target="load_games:get_batch"),
        Edge(source="dag:load_games", target="load_games:insert_to_staging"),
        Edge(source="load_games:get_batch", target="load_games:insert_to_staging"),
        Edge(source="table:INGESTION.NFL_GAME", target="load_games:insert_to_staging"),
        Edge(source="load_games:insert_to_staging", target="table:STAGING.NFL_GAME"),
        # ... more edges
    ]
)
```

**JSON Representation:** (`graph.to_json()`)

```json
{
  "nodes": [
    {
      "id": "dag:load_games",
      "label": "load_games",
      "type": "dag",
      "source_file": "examples/definitions/games.yml"
    },
    {
      "id": "load_games:get_batch",
      "label": "get_batch",
      "type": "task",
      "dag": "load_games",
      "operator": "PythonOperator",
      "source_file": "utils/get_batch.py"
    },
    {
      "id": "table:STAGING.NFL_GAME",
      "label": "STAGING.NFL_GAME",
      "type": "staging"
    }
  ],
  "edges": [
    {"source": "dag:load_games", "target": "load_games:get_batch"},
    {"source": "load_games:get_batch", "target": "load_games:insert_to_staging"},
    {"source": "table:INGESTION.NFL_GAME", "target": "load_games:insert_to_staging"},
    {"source": "load_games:insert_to_staging", "target": "table:STAGING.NFL_GAME"}
  ]
}
```

**Node Types:**

| Type | Color | Description |
|------|-------|-------------|
| `dag` | Yellow | DAG container |
| `task` | Green | Generic task (e.g., PythonOperator) |
| `source` | Purple | Source/ingestion tables |
| `staging` | Indigo | Staging layer tables |
| `dimension` | Pink | Dimension tables |
| `fact` | Teal | Fact tables |
| `table` | Blue | Generic table |

---

### Step 4: HTML Generation

**Function:** `lineage.generate_html(graph: LineageGraph, output_path: Path) -> str`

**Output:** Self-contained HTML file with embedded CSS and JavaScript

The generated HTML includes:
- D3.js and Dagre.js for graph layout
- Interactive features: zoom, pan, drag nodes
- Search functionality
- Filter by node type
- Click node to see details and highlight lineage
- Upstream/downstream filtering

---

## Usage

### CLI Commands

```bash
# Load and display DAGs from YAML files
dwat dags examples/definitions/

# Generate lineage visualization (coming soon)
dwat lineage examples/definitions/ --output lineage.html --open

# Parse SQL file (placeholder)
dwat parse examples/sql_scripts/staging/stg_game.sql
```

### Python API

```python
from pathlib import Path
from dwat.parsers.dag_parser import load_yamls
from dwat.lineage import build_graph_from_dags, generate_html, open_in_browser

# Step 1: Load YAML files
dags = load_yamls(Path("examples/definitions/"))

# Step 2: Build lineage graph
graph = build_graph_from_dags(dags)

# Step 3: Generate HTML visualization
output_path = Path("lineage.html")
generate_html(graph, output_path)

# Step 4: Open in browser
open_in_browser(output_path)
```

---

## Development

### Running Tests
```bash
pip install -e ".[dev]"
pytest
```

### Code Quality
```bash
# Format code
black dwat tests

# Lint code
ruff check dwat tests
```

## Roadmap

See `PROGRESS.md` for detailed status and roadmap.

**Current Phase:** Core lineage visualization in development

**Implemented:**
- YAML DAG parsing
- Lineage graph building
- Interactive HTML visualization (D3.js + Dagre)

**Future:**
- SQL parsing with sqlglot for table/column extraction
- Column-level lineage
- Advanced dependency analysis
- Performance metrics
- Export to other formats (JSON, Mermaid, etc.)

## Tech Stack
- **SQL Parsing:** sqlglot (multi-dialect support)
- **YAML Parsing:** PyYAML
- **CLI Framework:** Click
- **Visualization:** D3.js, Dagre.js, Dagre-D3
- **Target Deployment:** AWS/GCP (Docker)
