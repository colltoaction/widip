# widip/computer/yaml.py
from widip.yaml import load as yaml_load

def yaml(source: str):
    """Functor: parse and evaluate YAML source into a diagram."""
    return yaml_load(source)

eval_yaml = yaml
