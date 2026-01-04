from __future__ import annotations
from typing import Any
from discopy import closed
from . import representation as ren
from computer import Program, Data
from computer.core import Language

# Language is now a Ty instance
L = Language

def construct_scalar(box: ren.ScalarBox) -> closed.Diagram:
    if box.tag:
        # Program expects name and args
        args = (box.value,) if box.value is not None else ()
        return Program(box.tag, args)
    # Data expects value
    return Data(box.value)

def construct_sequence(box: ren.SequenceBox) -> closed.Diagram:
    import widip.yaml
    inside_computer = widip.yaml.construct_functor(box.inside)
    if box.tag:
        return Program(box.tag, (inside_computer,))
    return inside_computer

def construct_mapping(box: ren.MappingBox) -> closed.Diagram:
    import widip.yaml
    inside_computer = widip.yaml.construct_functor(box.inside)
    if box.tag:
        return Program(box.tag, (inside_computer,))
    return inside_computer
