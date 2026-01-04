from __future__ import annotations
from typing import Any
from discopy import closed
from . import representation as ren
from computer import Program, Data
from computer.core import Language

# Language is now a Ty instance
L = Language

def construct_scalar(box: ren.ScalarBox) -> closed.Diagram:
    # print(f"DEBUG: scalar tag={box.tag!r} value={box.value!r}")
    if box.tag:
        # Program expects name and args
        args = (box.value,) if box.value is not None else ()
        return Program(box.tag, args)
    if box.value is None or box.value == "":
        return closed.Id(Language)
    # Data expects value
    return Data(box.value)

def construct_sequence(box: ren.SequenceBox) -> closed.Diagram:
    import titi.yaml
    if box.tag == "titi":
        return construct_titi(ren.TitiBox(box.nested))
    inside_computer = titi.yaml.construct_functor(box.nested)
    if box.tag:
        return Program(box.tag, (inside_computer,))
    return inside_computer

def construct_mapping(box: ren.MappingBox) -> closed.Diagram:
    import titi.yaml
    from computer.common import TitiBox
    
    # Helper for structural Copy box
    def CopyBox():
        return TitiBox("Δ", Language, Language @ Language, data=(), draw_as_spider=True)

    inside_computer = titi.yaml.construct_functor(box.nested)
    
    # Implicitly copy input to all branches
    n = len(inside_computer.dom)
    if n > 1:
        def make_copy(k):
            if k <= 1: return closed.Id(Language)
            if k == 2: return CopyBox()
            return CopyBox() >> (closed.Id(Language) @ make_copy(k - 1))
        
        inside_computer = make_copy(n) >> inside_computer

    if box.tag == "titi":
        from computer import Titi
        return Titi.read_stdin >> inside_computer >> Titi.printer
    if box.tag:
        return Program(box.tag, (inside_computer,))
    return inside_computer

def construct_titi(box: ren.TitiBox) -> closed.Diagram:
    import titi.yaml
    from computer import Titi
    inside = titi.yaml.construct_functor(box.nested)
    # F(D) = stdin >> D >> printer
    # Use Titi services if available
    return Titi.read_stdin >> inside >> Titi.printer
