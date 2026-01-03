from __future__ import annotations
from typing import Any
from discopy import closed, monoidal
from .computer import Partial, Language, Program, Data

# --- DisCoPy Patch for Closed Types ---
# closed.Diagram uses monoidal.Hypergraph by default, which creates monoidal.Ty
# identities, causing type errors when combining with closed.Ty.
# We define a ClosedHypergraph that uses closed.Category.

class ClosedHypergraph(monoidal.Hypergraph):
    category = closed.Category

# Patch the factory
closed.Diagram.hypergraph_factory = ClosedHypergraph

# --------------------------------------

interpreter_box = Program("interpreter", Language @ Language, Language)
specializer_box = Program("specializer", Language @ Language, Language)

# Undecorated function for logic
def _specializer_impl(diagram, *args):
    return Partial(diagram, len(args))

@closed.Diagram.from_callable(Language @ Language, Language)
def specializer(program, *args):
    """
    Partial evaluator / Specializer.
    This function is called by DisCoPy to generate the diagram structure.
    It receives 'program' (a wire/box representing the program) and 'args' (wires/boxes representing inputs).
    """
    return specializer_box(program, *args)


def compiler(source):
    return _specializer_impl(interpreter_box, source)

# The compiler object (as a diagram/box)
# compiler = specializer(interpreter)
compiler_diagram = _specializer_impl(specializer_box, interpreter_box)

def compiler_generator():
    return _specializer_impl(specializer_box, specializer_box)
