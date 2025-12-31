from functools import reduce

from contextlib import contextmanager
from contextvars import ContextVar
from itertools import batched

from discopy import closed
from nx_hif.hif import HyperGraph

from . import hif
from .yaml import *

diagram_var: ContextVar[closed.Diagram] = ContextVar("diagram")

@contextmanager
def load_container(ob):
    token = diagram_var.set(ob)
    try:
        yield
    finally:
        diagram_var.reset(token)

def process_sequence(ob, tag):
    if tag:
        target = ob.cod
        exps, bases = get_exps_bases(target)
        ob = exps @ ob
        ob >>= closed.Eval(target)
        ob >>= Node(tag, ob.cod, closed.Ty() >> closed.Ty(tag))
    return ob

def process_mapping(ob, tag):
    # Mapping bubble is already applied before calling this
    if tag:
        target = ob.cod
        exps, bases = get_exps_bases(target)
        ob @= exps
        ob >>= closed.Eval(target)
        ob >>= Node(tag, ob.cod, closed.Ty(tag) >> closed.Ty(tag))
    return ob

def load_scalar(cursor, tag):
    data = hif.get_node_data(cursor)
    return Scalar(tag, data["value"])

def load_sequence(cursor, tag):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    items = list(diagrams)
    
    if not items:
        ob = Scalar(tag, "")
    else:
        diagram = reduce(lambda a, b: a @ b, items)
        ob = Sequence(diagram)
        ob = process_sequence(ob, tag)

    with load_container(ob):
        return diagram_var.get()

def load_mapping(cursor, tag):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    items = []

    for key, val in batched(diagrams, 2):
        pair = key @ val
        pair = Sequence(pair, n=2)
        items.append(pair)
    
    if not items:
        ob = Scalar(tag, "")
    else:
        diagram = reduce(lambda a, b: a @ b, items)
        ob = Mapping(diagram)
        ob = process_mapping(ob, tag)

    with load_container(ob):
        return diagram_var.get()

def incidences_to_diagram(node: HyperGraph):
    cursor = (0, node)
    return _incidences_to_diagram(cursor)

def _incidences_to_diagram(cursor):
    data = hif.get_node_data(cursor)
    tag = (data.get("tag") or "")[1:]
    kind = data["kind"]
    anchor = data.get("anchor")

    match kind:
        case "stream":
            ob = load_stream(cursor)
        case "document":
            ob = load_document(cursor)
        case "scalar":
            ob = load_scalar(cursor, tag)
        case "sequence":
            ob = load_sequence(cursor, tag)
        case "mapping":
            ob = load_mapping(cursor, tag)
        case "alias":
            ob = Alias(anchor, closed.Ty(), closed.Ty() >> closed.Ty(anchor))
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    if anchor and kind != 'alias':
        ob >>= Anchor(anchor, ob.cod, ob.cod)
    return ob

def load_document(cursor):
    root = hif.step(cursor, "next")
    return _incidences_to_diagram(root) if root else closed.Id()

def load_stream(cursor):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    return reduce(lambda a, b: a @ b, diagrams, closed.Id())
