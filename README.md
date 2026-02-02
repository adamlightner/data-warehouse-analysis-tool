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

## Usage

```bash
# Analyze files in a directory
dwat analyze /path/to/warehouse/files

# Recursively analyze subdirectories
dwat analyze /path/to/warehouse/files --recursive

# Show version
dwat version
```

## Development

### Project Structure
```
dwat/
├── dwat/
│   ├── parsers/      # SQL and YAML parsers
│   ├── analyzers/    # Analysis logic
│   └── cli.py        # CLI entry point
├── tests/            # Test suite
└── pyproject.toml    # Project configuration
```

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

**Current Phase:** Initial setup complete, core analysis features in development

**Future:**
- Interactive web frontend for exploration
- Advanced dependency analysis
- Column lineage tracking
- Performance metrics

## Tech Stack
- **SQL Parsing:** sqlglot (multi-dialect support)
- **YAML Parsing:** PyYAML
- **CLI Framework:** Click
- **Target Deployment:** AWS/GCP (Docker)
