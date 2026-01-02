from functools import reduce

from contextlib import contextmanager
from contextvars import ContextVar
from itertools import batched

from discopy import closed
from nx_hif.hif import HyperGraph

from . import hif
from .yaml import Scalar, Sequence, Mapping, Anchor, Alias
from .computer import Program, Language

diagram_var: ContextVar[closed.Diagram] = ContextVar("diagram")

@contextmanager
def load_container(cursor):
    token = diagram_var.set(cursor)
    try:
        yield hif.iterate(cursor)
    finally:
        diagram_var.reset(token)

def load_scalar(cursor, tag):
    data = hif.get_node_data(cursor)
    return Scalar(tag, data["value"])

def load_sequence(cursor, tag):
    diagrams = []
    with load_container(cursor) as items:
        for item in items:
            diagrams.append(_incidences_to_diagram(item))

    if not diagrams:
        ob = Scalar(tag, "")
    else:
        # Sequences are pipelines (sequential composition)
        ob = reduce(lambda a, b: a >> b, diagrams)

    if tag:
         ob = Sequence(ob, tag=tag)
    return ob

def load_mapping(cursor, tag):
    items = []
    with load_container(cursor) as nodes:
        diagrams_list = list(map(_incidences_to_diagram, nodes))
        for key, val in batched(diagrams_list, 2):
            if isinstance(key, Scalar) and not key.tag and not key.value:
                 continue
            # Mapping entries are Key >> Value (pipeline)
            items.append(key >> val)

    if not items:
        ob = Scalar(tag, "")
    else:
        # Implicitly copy input to all branches
        from .computer import Copy, Language
        from functools import reduce
        ob = Copy(Language, len(items)) >> reduce(lambda a, b: a @ b, items)
    
    if tag:
        ob = Mapping(ob, tag=tag)
    return ob

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
            ob = Alias(anchor)
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    if anchor and kind != 'alias':
        ob = Anchor(anchor, ob)
    return ob

def load_document(cursor):
    root = hif.step(cursor, "next")
    return _incidences_to_diagram(root) if root else closed.Id()

def load_stream(cursor):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    return reduce(lambda a, b: a @ b, diagrams, closed.Id())
