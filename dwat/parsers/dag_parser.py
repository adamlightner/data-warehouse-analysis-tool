import yaml
from pathlib import Path

def load_yamls(path: Path) -> dict:
    """Load YAML files."""
    dags = {}

    for path in path.rglob("*.yml"):
        with open(path) as f: 
            dags[str(path)] = yaml.safe_load(f)
        
    for path in path.rglob("*.yaml"):
        with open(path) as f: 
            dags[str(path)] = yaml.safe_load(f)

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