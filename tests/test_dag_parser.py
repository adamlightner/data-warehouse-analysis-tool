"""Tests for the DAG parser module."""

from pathlib import Path

from dwat.parsers.dag_parser import load_dag, load_dags, extract_tasks


EXAMPLES_DIR = Path(__file__).parent.parent / "examples" / "definitions"


def test_load_dag_returns_dict():
    dag = load_dag(EXAMPLES_DIR / "games.yml")
    assert isinstance(dag, dict)
    assert "load_games" in dag


def test_load_dag_has_tasks():
    dag = load_dag(EXAMPLES_DIR / "games.yml")
    tasks = dag["load_games"]["tasks"]
    assert isinstance(tasks, list)
    assert len(tasks) > 0


def test_load_dag_task_structure():
    dag = load_dag(EXAMPLES_DIR / "games.yml")
    tasks = dag["load_games"]["tasks"]
    first_task = tasks[0]
    assert "id" in first_task
    assert "op_type" in first_task


def test_load_dags_finds_all_files():
    dags = load_dags(EXAMPLES_DIR)
    assert len(dags) == 2
    filenames = [Path(k).name for k in dags.keys()]
    assert "games.yml" in filenames
    assert "teams.yml" in filenames


def test_load_dags_returns_valid_content():
    dags = load_dags(EXAMPLES_DIR)
    for path, dag_obj in dags.items():
        assert isinstance(dag_obj, dict)
        dag_name = list(dag_obj.keys())[0]
        assert "tasks" in dag_obj[dag_name]


def test_extract_tasks():
    dags = load_dags(EXAMPLES_DIR)
    tasks = extract_tasks(dags)
    assert len(tasks) > 0
    for dag_name, task_id, operator, source_file, params in tasks:
        assert isinstance(dag_name, str)
        assert isinstance(task_id, str)


def test_extract_tasks_has_params():
    dags = load_dags(EXAMPLES_DIR)
    tasks = extract_tasks(dags)
    tasks_with_params = [(name, tid, op, f, p) for name, tid, op, f, p in tasks if p]
    assert len(tasks_with_params) > 0
    for _, _, _, _, params in tasks_with_params:
        assert "TARGET_TABLE" in params
