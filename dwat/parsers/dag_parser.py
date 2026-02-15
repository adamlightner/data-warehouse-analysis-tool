import yaml
from pathlib import Path

def load_dag(file_name: Path) -> dict:
    """Load YAML file."""
    with open(file_name) as f: 
        return yaml.safe_load(f)

def load_dags(dir_name: Path) -> dict:
    """Load YAML files."""
    dags = {}

    for f in dir_name.rglob("*.yml"):
        dags[str(f)] = load_dag(f)
        
    for f in dir_name.rglob("*.yaml"):
        dags[str(f)] = load_dag(f)

    return dags

def extract_tasks(dag_list: list) -> list:
    """Extract tasks from DAG definition."""
    
    tasks = []

    for dag_file, dag_obj in dag_list.items():

        dag_name = list(dag_obj.keys())[0]
        dag_def = dag_obj[dag_name]
        
        for task in dag_def.get('tasks', None):
            
            id = task.get('id', None)
            operator = task.get('op_type', None)
            file = task.get('source_file', None)
            params = task.get('params', None)

            tasks.append((dag_name, id, operator, file, params))

    return tasks