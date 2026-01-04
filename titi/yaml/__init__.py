from __future__ import annotations
from typing import Any
from functools import singledispatch
import discopy
from discopy import symmetric, closed

from .parse import parse, impl_parse
from . import representation as ren
from .representation import Scalar, Sequence, Mapping, Alias, Document, Stream, Titi
from . import construct as con
from . import presentation as pres
from computer.core import Language

# --- Presentation Singletons ---

get_node_data = pres.GetNodeData()
step = pres.Step()
iterate = pres.Iterate()

# --- Compose Functor ---

@singledispatch
def compose_dispatch(box: Any) -> symmetric.Diagram:
    """Default dispatcher for serialization items."""
    return box

# Registrations
compose_dispatch.register(ren.YamlBox, lambda b: getattr(ren, f"comp_{b.kind[:3].lower()}")(b, compose_functor))

def _compose_ar(box):
    if hasattr(box, 'kind'):
         # YamlBox stores kind
         if box.kind == "Scalar": return ren.comp_sca(box)
         if box.kind == "Alias": return ren.comp_ali(box)
    elif hasattr(box, 'name'):
        if box.name == "Scalar": return ren.comp_sca(box)
        if box.name.startswith("Alias"): return ren.comp_ali(box)
    return compose_dispatch(box)

compose_functor = symmetric.Functor(ob={symmetric.Ty("Node"): ren.Node}, ar=_compose_ar)

@symmetric.Diagram.from_callable(symmetric.Ty("Node"), ren.Node)
def compose(node_wire):
    """Traceable compose diagram."""
    return symmetric.Box("compose", symmetric.Ty("Node"), ren.Node)(node_wire)

# --- Construct Functor ---

class MapAll:
    """Helper to map all types and objects to Language."""
    def __init__(self, target): self.target = target
    def __getitem__(self, _): return self.target
    def get(self, _, default=None): return self.target
    def __contains__(self, _): return True
    def __iter__(self): return iter([])

@singledispatch
def construct_dispatch(box: Any) -> closed.Diagram:
    # Handle raw closed.Box instances (Program, Data, etc.)
    if isinstance(box, closed.Box):
        return box >> closed.Id(box.cod)
    
    # Default for wires/nodes
    dom = getattr(box, 'dom', closed.Ty())
    return closed.Id(Language ** len(dom))

construct_dispatch.register(ren.YamlBox, con.construct_box)

# Original Functor that maps YamlBoxes to diagrams
_construct_functor = closed.Functor(
    ob=MapAll(Language), 
    ar=construct_dispatch, 
    cod=closed.Category()
)

def construct_functor(diag, *_, **__):
    """Compatibility wrapper for tests."""
    return _construct_functor(diag)

# --- Load Pipeline ---
load = lambda source: construct_functor(compose_functor(impl_parse(source)))
