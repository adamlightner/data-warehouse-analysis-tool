# DWAT - Data Warehouse Analysis Tool - Progress Tracker

## Project Overview
A tool to analyze SQL and YAML files for data warehouse logic. Built to parse generic SQL/YML files (not dbt-specific) and provide insights into warehouse structure and dependencies.

## Tech Stack
- **Language:** Python 3.11+
- **SQL Parser:** sqlglot (multi-dialect support)
- **YAML Parser:** PyYAML
- **CLI Framework:** Click
- **Visualization:** D3.js, Dagre.js (browser-based)
- **Testing:** pytest
- **Code Quality:** black, ruff

## Project Structure
```
data_warehouse_analysis_tool/
├── dwat/
│   ├── parsers/
│   │   ├── dag_parser.py      # YAML DAG parsing (load_dag, load_dags)
│   │   └── sql_parser.py      # SQL file loading + Jinja templating
│   ├── ui/
│   │   ├── template.html      # HTML template with CSS/JS/JSON placeholders
│   │   ├── styles.css         # Visualization styles
│   │   └── visualization.js   # D3.js/Dagre graph rendering
│   ├── lineage.py             # Graph building + HTML generation
│   ├── cli.py                 # CLI entry point (parse + lineage commands)
│   └── analyzers/             # Analysis logic (future)
├── examples/
│   ├── definitions/           # Sample YAML DAG files
│   └── sql/                   # Sample SQL files (staging/, fact/, dimension/)
├── tests/
├── pyproject.toml
├── README.md                  # Detailed workflow documentation
└── PROGRESS.md
```

---

## Completed

### Session 1 - Initial Setup (2025-02-01)
- [x] Project initialization with pip and venv (Python 3.12)
- [x] Created pyproject.toml with core dependencies
- [x] Set up directory structure
- [x] Created basic CLI entry point with Click
- [x] Added .gitignore and README.md

### Session 2 - DAG Lineage Visualization (2025-02-04)
- [x] Implemented YAML DAG parser (`dag_parser.py`)
- [x] Created lineage graph data structures (`Node`, `Edge`, `LineageGraph`)
- [x] Built graph construction from DAG definitions (`lineage.py`)
- [x] Created interactive HTML visualization template
  - [x] D3.js + Dagre for graph layout
  - [x] Search functionality
  - [x] Filter by node type
  - [x] Click to highlight lineage
  - [x] Upstream/downstream filtering
  - [x] Zoom, pan, drag nodes
  - [x] Info panel with node details
- [x] Added `dwat lineage` CLI command
- [x] Optimized edge rendering (thinner arrows, smooth curves on drag)
- [x] Added detailed comments to template.html for learning
- [x] Updated README with workflow documentation (input/output at each step)

### Session 3 - Multi-View Toggle & DAG Containers (2025-02-06)
- [x] Added view mode toggle button group (DAG, Table, Metric)
- [x] Implemented multi-view graph generation
  - [x] DAG view: Tasks colored by `op_type` (PythonOperator, SnowflakeOperator, etc.)
  - [x] Table view: Original graph with data layer colors (source, staging, fact, etc.)
  - [x] Metric view: Placeholder (same as Table for now)
- [x] DAG nodes now render as container boxes (compound/cluster nodes)
  - [x] Tasks visually grouped inside their parent DAG
  - [x] Lineage arrows between tasks based on `depends_on`
  - [x] DAG label at top of container
- [x] Updated `lineage.py` with `_build_dag_view()` and `_build_table_view()` functions
- [x] Added `generate_html_multi_view()` for embedding all view graphs
- [x] Fixed template.html placeholder issue (comments breaking JSON parsing)
- [x] Added CSS styles for operator types and cluster containers

### Session 4 - Table Lineage v1, CLI Refactor, Graph Improvements (2026-02-15)
- [x] Implemented Table Lineage v1 (YAML-driven)
  - [x] `_build_table_view()` extracts `TARGET_TABLE` + `*_TABLE` params from YAML tasks
  - [x] Direct table-to-table edges (source → target) built from params
  - [x] Table nodes colored by inferred data layer (source, staging, fact, dimension)
  - [x] `_infer_table_type()` guesses layer from table name prefixes
- [x] Refactored CLI (`cli.py`)
  - [x] Replaced flat `dags` command with `parse` group + subcommands (`parse dag`, `parse dags`, `parse sql`, `parse sqls`)
- [x] Refactored DAG parser (`dag_parser.py`)
  - [x] Renamed `load_yamls()` → `load_dags()`, split logic with `extract_tasks()`
- [x] Replaced `query_parser.py` with `sql_parser.py`
  - [x] `load_sql()`, `load_sqls()`, `format_sql()` (Jinja2 template rendering)
  - [x] Note: Loads/renders SQL files but does NOT parse SQL for lineage yet
- [x] Graph improvements in `lineage.py`
  - [x] Added transitive reduction (`_transitive_reduce()`) to remove redundant edges
  - [x] Added edge deduplication in `LineageGraph`
- [x] Moved example SQL files from `examples/sql_scripts/` → `examples/sql/`
- [x] Updated example YAML (`games.yml`) with additional `TEAM_TABLE` param

---

## Current Status

**Phase:** Table Lineage v1 Complete (YAML-driven) — SQL parsing next

**Working CLI Commands:**
```bash
dwat --help                              # Show help
dwat --version                           # Show version
dwat parse dag <file.yml>                # Load single DAG definition
dwat parse dags <dir>                    # Load all DAG definitions
dwat parse sql <file.sql> --context '{}' --verbose  # Load/render SQL file
dwat parse sqls <dir>                    # Load all SQL files
dwat lineage <path>                      # Generate interactive lineage HTML
dwat lineage <path> -o out.html --open   # Generate and open in browser
```

**Current Capabilities:**
- Parse Airflow-style YAML DAG definitions
- Extract tasks, dependencies, operators, parameters
- Multi-view toggle: DAG view (operator-based), Table view (data layer-based), Metric view (placeholder)
- DAG view shows tasks inside DAG container boxes with `depends_on` lineage
- Table view (v1) shows table-to-table lineage derived from YAML `*_TABLE` params
- Transitive reduction removes redundant edges from lineage graph
- Load and Jinja2-render SQL files with template variables
- Generate self-contained interactive HTML visualization

**Key Limitation:**
Table lineage currently relies entirely on YAML param metadata (`TARGET_TABLE`, `SOURCE_TABLE`, etc.). It does NOT parse SQL files to extract table dependencies. The `sqlglot` library is installed but unused.

---

## Next Steps - Lineage Types

### Phase 3: Multiple Lineage Views

The tool should support three distinct lineage perspectives:

#### 1. DAG Lineage (Current - Complete)
**What it shows:** DAG containers with tasks inside, colored by operator type
**Data source:** YAML DAG definition files
**Use case:** Understanding orchestration flow, task dependencies

```
┌─────────────────────────────────────────────────┐
│  load_games (DAG)                               │
│  ┌─────────────┐      ┌─────────────────────┐   │
│  │  get_batch  │ ───▶ │  insert_to_staging  │   │
│  │  (Python)   │      │    (Snowflake)      │   │
│  └─────────────┘      └─────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**Status:** ✅ Complete

---

#### 2. Table Lineage
**What it shows:** Source tables → Transformations → Target tables
**Data source:** YAML params (v1 - done) → SQL files via sqlglot (v2 - next)
**Use case:** Impact analysis, data flow understanding

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ INGESTION.GAME  │ ──▶ │  STAGING.GAME   │ ──▶ │   FACT.GAME     │
│    (source)     │     │   (transform)   │     │   (target)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**v1 (YAML-driven) — ✅ Complete:**
- [x] Extract `TARGET_TABLE` and `*_TABLE` params from YAML task definitions
- [x] Build direct table-to-table edges from params
- [x] Infer data layer (source/staging/fact/dimension) from table names
- [x] Color nodes by data layer in visualization
- [x] Toggle to Table view in UI button group

**v2 (SQL-driven) — TODO:**
- [ ] Implement SQL parser using sqlglot
  - [ ] Extract source tables (FROM, JOIN clauses)
  - [ ] Extract target tables (INSERT INTO, CREATE TABLE AS, MERGE INTO)
  - [ ] Handle CTEs and subqueries
  - [ ] Support template variables (`{{ TABLE_NAME }}`) — resolve from YAML params before parsing
- [ ] Build table-level lineage graph from SQL (replace or supplement YAML-driven approach)
- [ ] Merge SQL-parsed lineage with YAML metadata for context (operator type, DAG membership)
- [ ] Update visualization to indicate lineage source (SQL-parsed vs YAML-inferred)

---

#### 3. Column/Value Lineage (Future)
**What it shows:** Source columns → Transformations → Target columns
**Data source:** SQL files (deep parsing with sqlglot)
**Use case:** GDPR compliance, debugging data issues, understanding transformations

```
┌─────────────────────────────────────────────────────────────────┐
│  SOURCE.game_date  ──▶  CAST(...)  ──▶  TARGET.game_date_key   │
│  SOURCE.home_team  ──▶  UPPER(...)  ──▶  TARGET.home_team_name │
│  SOURCE.score      ──┬──▶  SUM(...)  ──▶  TARGET.total_score   │
│  SOURCE.score      ──┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

**TODO:**
- [ ] Extend SQL parser for column-level extraction
  - [ ] Map SELECT expressions to source columns
  - [ ] Track transformations (functions, CASE, aggregations)
  - [ ] Handle aliases and column renaming
  - [ ] Parse WHERE/GROUP BY for filtering context
- [ ] Build column-level lineage graph
- [ ] Add `dwat column-lineage <path>` CLI command
- [ ] Update visualization for column-level view
  - [ ] Expandable nodes (click table to see columns)
  - [ ] Transformation labels on edges

---

### Implementation Order

| Priority | Feature | Complexity | Value | Status |
|----------|---------|------------|-------|--------|
| 1 | Table Lineage v1 (YAML params) | Medium | High | ✅ Done |
| 2 | Table Lineage v2 (SQL parsing via sqlglot) | Medium | High - True lineage from SQL | **Next** |
| 3 | Combined View (UI toggle) | Medium | Medium - Toggle between views | ✅ Done |
| 4 | Column Lineage | High | High - Compliance/debugging | Todo |
| 5 | Export Options | Low | Medium - JSON, Mermaid, etc. | Todo |

---

## Long-Term Goal: Dynamic Web Application

### Vision
Evolve from static HTML generation to a full dynamic web application with API backend, enabling live updates, multi-user support, and richer features.

### Architecture Evolution

**Current (Static):**
```
YAML/SQL Files ──▶ Python (one-time) ──▶ lineage.html ──▶ Browser (file://)
```

**Future (Dynamic):**
```
┌─────────────┐     ┌─────────────────────────────────┐     ┌─────────┐
│  YAML/SQL   │     │         Python Server           │     │ Browser │
│   Files     │ ◀─▶ │  FastAPI + API Endpoints        │ ◀─▶ │ React/  │
│  (watched)  │     │  /api/lineage, /api/nodes, etc. │     │ Vue/JS  │
└─────────────┘     └─────────────────────────────────┘     └─────────┘
```

### Hybrid Approach (Recommended Path)

Keep static export while adding dynamic development mode:

```bash
# Static generation (current - always keep this)
dwat lineage examples/ -o lineage.html

# Dynamic local server (future)
dwat serve examples/ --port 8000
```

### API Endpoints (Future)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/lineage` | GET | Full lineage graph |
| `/api/lineage?mode=dag\|table\|column` | GET | Filtered by lineage type |
| `/api/nodes/{id}` | GET | Single node details |
| `/api/nodes/{id}/upstream` | GET | Upstream lineage |
| `/api/nodes/{id}/downstream` | GET | Downstream lineage |
| `/api/search?q=term` | GET | Search nodes |
| `/api/files` | GET | List parsed files |
| `/api/refresh` | POST | Re-parse source files |

### Tech Stack (Future)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **API Framework** | FastAPI | Async, auto-docs, type hints |
| **File Watching** | watchdog | Detect YAML/SQL changes |
| **Frontend** | React or Vue | Component-based, good D3 integration |
| **State** | Zustand or Pinia | Lightweight state management |
| **WebSocket** | FastAPI WS | Live updates on file change |

### Features Enabled by Dynamic Architecture

| Feature | Static | Dynamic |
|---------|--------|---------|
| View lineage | ✅ | ✅ |
| Share via file | ✅ | ❌ |
| Live file watching | ❌ | ✅ |
| Auto-refresh on change | ❌ | ✅ |
| User authentication | ❌ | ✅ |
| Multi-user collaboration | ❌ | ✅ |
| Persistent annotations | ❌ | ✅ |
| Search across projects | ❌ | ✅ |
| Database storage | ❌ | ✅ |
| Diff between versions | ❌ | ✅ |
| Impact analysis alerts | ❌ | ✅ |

### Implementation Phases

**Phase A: Local Dev Server**
- [ ] Add `dwat serve` command
- [ ] FastAPI with basic endpoints
- [ ] Serve existing UI from server
- [ ] File watching with auto-refresh

**Phase B: API-First Frontend**
- [ ] Refactor JS to fetch from API instead of embedded JSON
- [ ] Add loading states and error handling
- [ ] WebSocket for live updates

**Phase C: Enhanced Features**
- [ ] Search API with fuzzy matching
- [ ] Diff view (compare lineage over time)
- [ ] Annotations/comments on nodes
- [ ] User preferences (saved filters, layouts)

**Phase D: Production Deployment**
- [ ] Docker containerization
- [ ] Authentication (OAuth, API keys)
- [ ] PostgreSQL for metadata storage
- [ ] Deploy to AWS/GCP

---

## Open Questions

1. **SQL Dialect:** Should we auto-detect or require explicit dialect flag?
   - sqlglot supports: Snowflake, BigQuery, Redshift, Postgres, etc.

2. **Template Variables:** How to handle `{{ VAR }}` in SQL?
   - Option A: Require params file to resolve
   - Option B: Parse as-is, show as placeholder nodes
   - Option C: Regex replace before parsing

3. ~~**Visualization Mode:** Single view that toggles, or separate commands?~~
   - ✅ **Resolved:** Using in-UI toggle buttons (DAG, Table, Metric)

5. **SQL-Parsed vs YAML-Inferred Lineage:** When SQL parsing is implemented, should it fully replace YAML-driven table lineage, or supplement it?
   - Option A: SQL-parsed overrides YAML params (SQL is source of truth)
   - Option B: Merge both — SQL-parsed edges + YAML params as fallback for tasks without SQL
   - Option C: Show both with visual distinction (confidence indicator)

4. **Incremental Parsing:** For large warehouses, parse all SQL upfront or on-demand?

---

## Notes
- Using CDNs for D3/Dagre (can bundle later with `--bundle` flag)
- Template HTML is heavily commented for learning purposes
- README contains detailed input/output examples for each workflow step
