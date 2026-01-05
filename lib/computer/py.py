# titi/computer/py.py
import ast
import functools
import operator
from discopy import closed

def py(code: str):
    """Functor str → AST → object: parse and evaluate Python expressions via AST."""
    return eval(compile(ast.parse(code, mode='eval'), '<string>', 'eval'))

eval_python = py
