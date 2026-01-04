from __future__ import annotations
from typing import Any
from discopy import closed
from . import representation as ren
from computer import Program, Data, Titi, Discard
from computer.core import Language
from computer.common import TitiBox
import sys

# Language is now a Ty instance
L = Language

def debug_log(msg):
    with open("construct_debug.log", "a") as f:
        f.write(msg + "\n")

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
    name = getattr(box, 'name', 'Unknown')
    debug_log(f"Constructing {name}, Tag={tag}, Value={value!r}, Nested={nested!r}")

    # 1. Handle Titi Special Case
    if tag == "titi":
        inside = titi.yaml.construct_functor(nested)
        start = Titi.read_stdin
        if not inside.dom: start = start >> Discard()
        return start >> inside >> Titi.printer

    # 2. Handle Scalar (Leaf)
    if nested is None:
        if tag:
            # Program with static arg
            args = (value,) if value is not None else ()
            debug_log(f"  -> Program({tag}, {args})")
            return Program(tag, args)
        if value is None or value == "":
            debug_log(f"  -> Identity")
            return closed.Id(Language)
        debug_log(f"  -> Data({value})")
        return Data(value)

    # 3. Handle Container (Sequence / Mapping)
    debug_log("  -> Recursing functor")
    inside = titi.yaml.construct_functor(nested)
    debug_log(f"  -> Inside constructed: {inside}")
    
    # Implicit Input Copying for Mappings
    if isinstance(box, ren.MappingBox):
        n = len(inside.dom)
        debug_log(f"  -> MappingBox n={n}")
        if n > 1:
            inside = make_copy(n) >> inside

    # 4. Handle Tags on Containers (Generic Program Wrapper)
    if tag:
        # Simplify argument extraction:
        # If the container contains only data/scalars, we might want to pass them as args?
        # For now, we wrap the inside diagram as a generic argument/program input.
        # This matches the previous logic: Program(box.tag, (inside_computer,))
        debug_log(f"  -> Wrapping in Program({tag})")
        return Program(tag, (inside,))

    return inside
