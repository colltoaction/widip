from __future__ import annotations
from typing import Any
from discopy import closed
from . import representation as ren
from ..computer import Program, Data
from ..core import Language

# Language is now a Ty instance, so we can use it directly
L = Language

def construct_scalar(box: ren.ScalarBox) -> closed.Diagram:
    args = (box.value,) if box.value is not None else ()
    if box.tag:
         return Program(box.tag, L ** len(box.dom), L ** len(box.cod), args)
    return Data(box.value, L ** len(box.dom), L ** len(box.cod))

def construct_sequence(box: ren.SequenceBox) -> closed.Diagram:
    from . import construct
    inside_computer = construct(box.inside)
    if box.tag:
        return Program(box.tag, L ** len(box.dom), L ** len(box.cod), (inside_computer,))
    return inside_computer

def construct_mapping(box: ren.MappingBox) -> closed.Diagram:
    from . import construct
    inside_computer = construct(box.inside)
    if box.tag:
        return Program(box.tag, L ** len(box.dom), L ** len(box.cod), (inside_computer,))
    return inside_computer
