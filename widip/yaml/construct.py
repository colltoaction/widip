from __future__ import annotations
from typing import Any
from functools import singledispatch
from discopy import closed
from .representation import Scalar, Sequence, Mapping
from ..computer import Program, Data, Language

# Language is now a Ty instance, so we can use it directly
L = Language

# Functor mapping NodeGraph (Semantic) to Computer (Execution)
@closed.Diagram.from_callable(L, L)
def construct(box: Any) -> closed.Diagram:
    """Functor entry point mapping NodeGraph to Computer diagrams."""
    return construct_dispatch(box)

@singledispatch
def construct_dispatch(box: Any) -> closed.Diagram:
    """Default dispatcher acting as identity for wires."""
    return closed.Id(L ** len(box.dom))

def construct_scalar(box: Scalar) -> closed.Diagram:
    args = (box.value,) if box.value is not None else ()
    if box.tag:
         return Program(box.tag, L ** len(box.dom), L ** len(box.cod), args)
    return Data(box.value, L ** len(box.dom), L ** len(box.cod))

construct_dispatch.register(Scalar, construct_scalar)

def construct_sequence(box: Sequence) -> closed.Diagram:
    inside_computer = construct(box.inside)
    if box.tag:
        return Program(box.tag, L ** len(box.dom), L ** len(box.cod), (inside_computer,))
    return inside_computer

construct_dispatch.register(Sequence, construct_sequence)

def construct_mapping(box: Mapping) -> closed.Diagram:
    inside_computer = construct(box.inside)
    if box.tag:
        return Program(box.tag, L ** len(box.dom), L ** len(box.cod), (inside_computer,))
    return inside_computer

construct_dispatch.register(Mapping, construct_mapping)
