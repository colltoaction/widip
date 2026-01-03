from __future__ import annotations
from typing import Any
from functools import singledispatch
from discopy import symmetric, closed

from .parse import parse
from . import serialization as ser
from . import representation as ren
from . import construct as con
from . import presentation as pres
from ..computer import Language

# --- Presentation Singletons ---

get_node_data = pres.GetNodeData()
step = pres.Step()
iterate = pres.Iterate()

# --- Compose Functor: Serialization -> Semantic (Representation) ---

@singledispatch
def compose_dispatch(box: Any) -> symmetric.Diagram:
    """Default dispatcher for serialization nodes."""
    return box

compose_dispatch.register(ser.Sequence, lambda box: ren.Sequence(compose(box.inside), tag=box.tag))
compose_dispatch.register(ser.Mapping, lambda box: ren.Mapping(compose(box.inside), tag=box.tag))
compose_dispatch.register(ser.Document, lambda box: ren.Document(compose(box.inside)))
compose_dispatch.register(ser.Stream, lambda box: ren.Stream(compose(box.inside)))
compose_dispatch.register(ser.Anchor, lambda box: ren.Anchor(box.name, compose(box.inside)))
compose_dispatch.register(ser.Scalar, lambda box: ren.Scalar(box.tag, box.value))
compose_dispatch.register(ser.Alias, lambda box: ren.Alias(box.name))

@symmetric.Diagram.from_callable(ser.Node, ren.Node)
def compose(box: Any) -> symmetric.Diagram:
    """Functorial mapping: Serialization Tree -> Semantic Node Graph."""
    return compose_dispatch(box)

# --- Construct Functor: Semantic (Representation) -> Computer ---

@singledispatch
def construct_dispatch(box: Any) -> closed.Diagram:
    """Default dispatcher acting as identity for wires."""
    return closed.Id(Language ** len(box.dom))

construct_dispatch.register(ren.ScalarBox, con.construct_scalar)
construct_dispatch.register(ren.SequenceBox, con.construct_sequence)
construct_dispatch.register(ren.MappingBox, con.construct_mapping)

@closed.Diagram.from_callable(Language, Language)
def construct(box: Any) -> closed.Diagram:
    """Functor entry point mapping NodeGraph to Computer diagrams."""
    return construct_dispatch(box)

# --- Load Pipeline ---

load = parse >> compose >> construct
