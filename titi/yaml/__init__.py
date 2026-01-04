from __future__ import annotations
from typing import Any
from functools import singledispatch
from discopy import symmetric, closed

from .parse import parse, impl_parse, SequenceBox, MappingBox, AnchorBox, DocumentBox, StreamBox
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

# Registrations using functions from representation
compose_dispatch.register(SequenceBox, lambda b: ren.comp_seq(b, compose_functor))
compose_dispatch.register(MappingBox, lambda b: ren.comp_map(b, compose_functor))
compose_dispatch.register(AnchorBox, lambda b: ren.comp_anc(b, compose_functor))
compose_dispatch.register(DocumentBox, lambda b: ren.comp_doc(b, compose_functor))
compose_dispatch.register(StreamBox, lambda b: ren.comp_str(b, compose_functor))

def _compose_ar(box):
    if hasattr(box, 'name'):
        if box.name == "Scalar": return ren.comp_sca(box)
        if box.name.startswith("Alias"): return ren.comp_ali(box)
    return compose_dispatch(box)

compose_functor = symmetric.Functor(ob={symmetric.Ty("Node"): ren.Node}, ar=_compose_ar)

@symmetric.Diagram.from_callable(symmetric.Ty("Node"), ren.Node)
def compose(node_wire):
    """Traceable compose diagram."""
    return symmetric.Box("compose", symmetric.Ty("Node"), ren.Node)(node_wire)

# --- Construct Functor ---

@singledispatch
def construct_dispatch(box: Any) -> closed.Diagram:
    # Default for wires/nodes
    if not hasattr(box, 'dom'): 
        # For Identiy boxes, dom might be Ty("Node")
        return closed.Id(Language)
    # Ensure we use closed.Ty for powers
    return closed.Id(Language**len(box.dom))

construct_dispatch.register(ren.ScalarBox, con.construct_box)
construct_dispatch.register(ren.SequenceBox, con.construct_box)
construct_dispatch.register(ren.MappingBox, con.construct_box)
construct_dispatch.register(ren.DocumentBox, lambda b: construct_dispatch(b.nested))
construct_dispatch.register(ren.StreamBox, lambda b: construct_dispatch(b.nested))
construct_dispatch.register(ren.AnchorBox, con.construct_box)
construct_dispatch.register(ren.AliasBox, con.construct_box)
construct_dispatch.register(ren.TitiBox, con.construct_box)

construct_functor = closed.Functor(
    ob={
        "Node": Language, 
        "P": Language,
        ren.Node: Language,
        closed.Ty("Node"): Language,
        closed.Ty("P"): Language
    }, 
    ar=construct_dispatch, 
    cod=closed.Category()
)

# --- Load Pipeline ---
load = lambda source: construct_functor(compose_functor(impl_parse(source)))
