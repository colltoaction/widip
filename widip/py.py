"""
Bootstrap functors for self-hosting widip via Futamura projections.

eval_diagram: (tuple, ⊗) → (tuple, ⊗)  -- monoid homomorphism, flattens nested tuples
eval_python:  str → AST → object       -- parses and evaluates Python AST for self-hosting
"""

import functools, operator, ast
from . import computer

@computer.Program.as_diagram()
def eval_diagram(tuples):
    """Monoid homomorphism: flatten tuple of tuples via reduce(add, tuples, ())."""
    return functools.reduce(operator.add, tuples, ())

@computer.Program.as_diagram()
def eval_python(code):
    """Functor str → AST → object: parse and evaluate Python expressions via AST."""
    return eval(compile(ast.parse(code, mode='eval'), '<string>', 'eval'))
