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
│   │   ├── dag_parser.py      # YAML DAG parsing
│   │   └── query_parser.py    # SQL parsing (placeholder)
│   ├── ui/
│   │   ├── template.html      # HTML template (commented for learning)
│   │   ├── styles.css         # Visualization styles
│   │   └── visualization.js   # D3.js/Dagre graph rendering
│   ├── lineage.py             # Graph building + HTML generation
│   ├── cli.py                 # CLI entry point
│   └── analyzers/             # Analysis logic (future)
├── examples/
│   ├── definitions/           # Sample YAML DAG files
│   └── sql_scripts/           # Sample SQL files
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

---

## Current Status

**Phase:** DAG Lineage MVP Complete

**Working CLI Commands:**
```bash
dwat --help                    # Show help
dwat --version                 # Show version
dwat dags <path>               # Load and display DAG tasks
dwat lineage <path>            # Generate interactive lineage HTML
dwat lineage <path> -o out.html --open  # Generate and open in browser
```

**Current Capabilities:**
- Parse Airflow-style YAML DAG definitions
- Extract tasks, dependencies, operators, parameters
- Build directed graph of DAG → Task → Table relationships
- Generate self-contained interactive HTML visualization

---

## Next Steps - Lineage Types

### Phase 3: Multiple Lineage Views

The tool should support three distinct lineage perspectives:

#### 1. DAG Lineage (Current - MVP Complete)
**What it shows:** Airflow DAGs → Tasks → Dependencies
**Data source:** YAML DAG definition files
**Use case:** Understanding orchestration flow, task dependencies

```
┌─────────┐     ┌───────────┐     ┌─────────────┐
│   DAG   │ ──▶ │   Task    │ ──▶ │    Task     │
│load_game│     │ get_batch │     │insert_to_stg│
└─────────┘     └───────────┘     └─────────────┘
```

**Status:** ✅ Complete

---

#### 2. Table Lineage (Next Priority)
**What it shows:** Source tables → Transformations → Target tables
**Data source:** SQL files (parsed with sqlglot)
**Use case:** Impact analysis, data flow understanding

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ INGESTION.GAME  │ ──▶ │  STAGING.GAME   │ ──▶ │   FACT.GAME     │
│    (source)     │     │   (transform)   │     │   (target)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**TODO:**
- [ ] Implement SQL parser using sqlglot
  - [ ] Extract source tables (FROM, JOIN clauses)
  - [ ] Extract target tables (INSERT INTO, CREATE TABLE AS, MERGE INTO)
  - [ ] Handle CTEs and subqueries
  - [ ] Support template variables (`{{ TABLE_NAME }}`)
- [ ] Build table-level lineage graph
- [ ] Add `dwat table-lineage <path>` CLI command
- [ ] Update visualization to show table relationships

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

| Priority | Feature | Complexity | Value |
|----------|---------|------------|-------|
| 1 | Table Lineage | Medium | High - Most requested feature |
| 2 | Column Lineage | High | High - Compliance/debugging |
| 3 | Combined View | Medium | Medium - Toggle between views |
| 4 | Export Options | Low | Medium - JSON, Mermaid, etc. |

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

3. **Visualization Mode:** Single view that toggles, or separate commands?
   - `dwat lineage --mode dag|table|column`
   - vs. `dwat dag-lineage`, `dwat table-lineage`, `dwat column-lineage`

4. **Incremental Parsing:** For large warehouses, parse all SQL upfront or on-demand?

---

## Notes
- Using CDNs for D3/Dagre (can bundle later with `--bundle` flag)
- Template HTML is heavily commented for learning purposes
- README contains detailed input/output examples for each workflow step
