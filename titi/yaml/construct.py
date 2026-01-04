from __future__ import annotations
from typing import Any
from discopy import closed
from . import representation as ren
from computer import Program, Data, Titi, Discard
from computer.core import Language
from computer.common import TitiBox

# Language is now a Ty instance
L = Language

def CopyBox():
    return TitiBox("Δ", Language, Language @ Language, data=(), draw_as_spider=True)

def make_copy(n):
    if n <= 1: return closed.Id(Language)
    if n == 2: return CopyBox()
    return CopyBox() >> (closed.Id(Language) @ make_copy(n - 1))

def construct_box(box) -> closed.Diagram:
    import titi.yaml
    
    tag = getattr(box, 'tag', None)
    value = getattr(box, 'value', None)
    nested = getattr(box, 'nested', None)
    name = getattr(box, 'name', None) # For Alias/Anchor

    # 1. Handle Titi Special Case
    if tag == "titi":
        inside = titi.yaml.construct_functor(nested)
        start = Titi.read_stdin
        if not inside.dom: start = start >> Discard()
        return start >> inside >> Titi.printer

    # 2. Handle Anchor (Wrap inside with program)
    if isinstance(box, ren.AnchorBox):
        inside = titi.yaml.construct_functor(nested)
        return Program("anchor", (name, inside))

    # 3. Handle Alias (Leaf with name)
    if isinstance(box, ren.AliasBox):
        return Program("alias", (name,))

    # 4. Handle Scalar (Leaf)
    if nested is None:
        if tag:
            args = (value,) if value is not None else ()
            return Program(tag, args)
        if value is None or value == "":
            return closed.Id(Language)
        return Data(value)

    # 5. Handle Container (Sequence / Mapping)
    inside = titi.yaml.construct_functor(nested)
    
    # Implicit Input Copying for Mappings
    if isinstance(box, ren.MappingBox):
        n = len(inside.dom)
        if n > 1:
            inside = make_copy(n) >> inside

    # 6. Handle Tags on Containers (Generic Program Wrapper)
    if tag:
        return Program(tag, (inside,))

    return inside
