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

def extract_args(box):
    """Recursively extract static arguments from boxes."""
    if isinstance(box, ren.ScalarBox):
        return (str(box.value),)
    if hasattr(box, 'nested'): # Sequence, Mapping
        # For Sequence: boxes are in nested (Diagram)
        # For Mapping: keys are in nested (Diagram) ?? 
        # Mapping structure is Key >> Value tensor.
        # This is hard to robustly extract from a Diagram topology.
        # But if it's simple data sequence, it might be just boxes in parallel or sequence.
        
        args = []
        for b in box.nested.boxes:
             args.extend(extract_args(b))
        return tuple(args)
    # If structural box like Copy/Id handling in Diagram:
    return ()

def construct_sequence(box: ren.SequenceBox) -> closed.Diagram:
    import titi.yaml
    if box.tag == "titi":
        return construct_titi(ren.TitiBox(box.nested))
    
    # Try to extract static args if tagged
    if box.tag:
         try:
             args = extract_args(box)
             if args:
                 return Program(box.tag, args)
         except: pass

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

    # Try to extract static args if tagged (e.g. !tr {a, b})
    if box.tag:
         try:
             args = extract_args(box)
             # Note: Extracting from Mapping Diagram (key>>value) is tricky.
             # Keys are often Scalars. Values might be None.
             # "Key >> Value" -> Scalar box followed by Value box?
             # If value is Identity (None), it's just Scalar.
             # So we might find Scalar boxes.
             # But parallel mappings are tensors.
             if args:
                 return Program(box.tag, args)
         except: pass

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
        return construct_titi(ren.TitiBox(box.nested))
    if box.tag:
        return Program(box.tag, (inside_computer,))
    return inside_computer

def construct_titi(box: ren.TitiBox) -> closed.Diagram:
    import titi.yaml
    from computer import Titi, Discard
    inside = titi.yaml.construct_functor(box.nested)
    # F(D) = stdin >> D >> printer
    
    start = Titi.read_stdin
    if not inside.dom:
         start = start >> Discard()
    
    return start >> inside >> Titi.printer
