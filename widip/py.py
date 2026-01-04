"""
Bootstrap functors for self-hosting widip via Futamura projections.

eval_diagram: (tuple, ⊗) → (tuple, ⊗)  -- monoid homomorphism, flattens nested tuples
eval_python:  str → AST → object       -- parses and evaluates Python AST for self-hosting
"""

import functools, operator, ast
from discopy import python

eval_diagram: python.Ty = lambda tuples: functools.reduce(operator.add, tuples, ())
eval_diagram.__doc__ = """Monoid homomorphism: flatten tuple of tuples via reduce(add, tuples, ())."""

eval_python: python.Ty = lambda code: eval(compile(ast.parse(code, mode='eval'), '<string>', 'eval'))
eval_python.__doc__ = """Functor str → AST → object: parse and evaluate Python expressions via AST."""
