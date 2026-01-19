from discopy import closed
from ..common import TitiBox
from ..core import Language
import functools, operator, ast

class Eval(TitiBox):
    def __init__(self, dom_type=Language, cod_type=Language):
        super().__init__("{−}", Language @ dom_type, cod_type)

class PartialEval(TitiBox):
    def __init__(self):
        super().__init__("[−]", Language @ Language, Language)

def eval_diagram(tuples):
    return functools.reduce(operator.add, tuples, ())

def eval_python(code: str):
    return eval(compile(ast.parse(code, mode='eval'), '<string>', 'eval'))

def eval_yaml(source: str):
    from computer.yaml import load
    return load(source)

__all__ = ["Eval", "PartialEval", "eval_diagram", "eval_python", "eval_yaml"]
