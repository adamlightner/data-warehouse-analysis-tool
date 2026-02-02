# DWAT - Data Warehouse Analysis Tool - Progress Tracker

## Project Overview
A tool to analyze SQL and YAML files for data warehouse logic. Built to parse generic SQL/YML files (not dbt-specific) and provide insights into warehouse structure and dependencies.

**Future Goal:** Add interactive web frontend for exploration (Phase 2)

## Tech Stack Decisions
- **Language:** Python 3.11+
- **SQL Parser:** sqlglot (multi-dialect support, powerful parsing)
- **YAML Parser:** PyYAML
- **CLI Framework:** Click
- **Dependency Management:** pip + pyproject.toml
- **Testing:** pytest
- **Code Quality:** black, ruff
- **Deployment Target:** AWS/GCP (Docker containers)

## Project Structure
```
data_warehouse_analysis_tool/
├── dwat/                  # Main package
│   ├── parsers/          # SQL and YAML parsers
│   ├── analyzers/        # Analysis logic
│   └── cli.py            # CLI entry point
├── tests/                # Test suite
├── venv/                 # Virtual environment
├── pyproject.toml        # Project config and dependencies
└── PROGRESS.md           # This file
```

## Completed

### Session 1 - Initial Setup (2026-02-01)
- [x] Project initialization with pip and venv (Python 3.12.12)
- [x] Created pyproject.toml with core dependencies
- [x] Set up directory structure (dwat package with parsers/ and analyzers/)
- [x] Created PROGRESS.md for session tracking
- [x] Installed dependencies (sqlglot 28.7.0, pyyaml 6.0.3, click 8.3.1)
- [x] Created basic CLI entry point with Click framework
- [x] Tested CLI commands (`dwat --help`, `dwat analyze`)
- [x] Added .gitignore for Python projects
- [x] Created README.md with setup and usage instructions

## Current Status
**Phase:** Initial Setup Complete - Ready for Core Development

**Working CLI Commands:**
- `dwat --help` - Show help
- `dwat analyze <path>` - Analyze files (placeholder implementation)
- `dwat version` - Show version

## Next Steps
1. Implement SQL parser wrapper around sqlglot
2. Implement YAML parser
3. Design core analysis features (what to extract from SQL/YML)
4. Build initial analyzers (table dependencies, query structure, etc.)
5. Add unit tests for parsers
6. Implement output formatting (JSON, reports)

## Open Questions / Decisions Needed
- What specific analyses do we want to perform? (e.g., table dependencies, column lineage, query complexity)
- What should the output format be? (JSON, Markdown reports, etc.)
- Do we need to support specific SQL dialects or be dialect-agnostic?

## Notes
- Using `dwat` as the CLI command and package name
- Structured for future expansion with web frontend
- Built with production deployment in mind (Docker-ready)
