from __future__ import annotations
from typing import Any
import discopy
from discopy import frobenius, closed

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

def compose_dispatch(box: Any) -> frobenius.Diagram:
    """Manual dispatcher for serialization items."""
    if hasattr(box, 'kind'):
         kind = box.kind
         if kind == "Scalar": return ren.Scalar(box.tag, box.value)
         if kind == "Alias": return ren.Alias(box.anchor_name)
    return box

compose_functor = frobenius.Functor(ob={frobenius.Ty("Node"): ren.Node}, ar=compose_dispatch)

@frobenius.Diagram.from_callable(frobenius.Ty("Node"), ren.Node)
def compose(node_wire):
    """Traceable compose diagram."""
    return frobenius.Box("compose", frobenius.Ty("Node"), ren.Node)(node_wire)

# --- Construct Functor ---

class MapAll:
    """Helper to map all types and objects to Language."""
    def __init__(self, target): self.target = target
    def __getitem__(self, _): return self.target
    def get(self, _, default=None): return self.target
    def __contains__(self, _): return True
    def __iter__(self): return iter([])

def construct_dispatch(box: Any) -> closed.Diagram:
    # Handle raw closed.Box instances (Program, Data, etc.)
    if isinstance(box, closed.Box):
        return box >> closed.Id(box.cod)
    
    if isinstance(box, ren.YamlBox):
        return con.construct_box(box)
    
    # Default for wires/nodes
    dom = getattr(box, 'dom', closed.Ty())
    return closed.Id(Language ** len(dom))

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
