# titi/computer/yaml.py
import functools
import operator
from computer.yaml import load as yaml_load

def yaml(source: str):
    """Functor: parse and evaluate YAML source into a diagram."""
    return yaml_load(source)

eval_yaml = yaml

def eval_diagram(tuples):
    """Monoid homomorphism: flatten tuple of tuples via reduce(add, tuples, ())."""
    return functools.reduce(operator.add, tuples, ())
