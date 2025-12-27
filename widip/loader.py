from functools import reduce
from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.closed import Id, Ty, Box, Eval

from .traverse import vertical_map, get_base, get_fiber
from . import hif
from .yaml import Scalar, Sequence, Mapping, NODE

def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams

def incidences_to_diagram(node: HyperGraph):
    # TODO properly skip stream and document start
    cursor = (0, node)
    diagram = _incidences_to_diagram(cursor)
    return diagram

def _incidences_to_diagram(cursor):
    """
    Takes an nx_yaml rooted bipartite graph
    and returns an equivalent string diagram
    """
    node = get_base(cursor)
    index = get_fiber(cursor)

    tag = (hif_node(node, index).get("tag") or "")[1:]
    kind = hif_node(node, index)["kind"]

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
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    return ob

def load_scalar(cursor, tag):
    node = get_base(cursor)
    index = get_fiber(cursor)

    v = hif_node(node, index)["value"]

    # Handle empty value (empty string or empty Ty) as None
    if hasattr(v, "__len__") and len(v) == 0:
        v = None

    # Return Scalar with value and tag
    return Scalar(v, tag=tag)

def load_pair(pair):
    key, value = pair
    return key @ value

def load_mapping(cursor, tag):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    kvs = batched(diagrams, 2)

    kv_diagrams = list(map(load_pair, kvs))

    if not kv_diagrams:
        ob = Mapping(Ty()) # Empty mapping
    else:
        ob = reduce(lambda a, b: a @ b, kv_diagrams)
        ob = ob >> Mapping(ob.cod)

    if tag:
        tag_box = Box(tag, NODE, NODE)
        ob = ob >> tag_box
    return ob

def load_sequence(cursor, tag):
    diagrams_list = list(map(_incidences_to_diagram, hif.iterate(cursor)))

    if not diagrams_list:
        ob = Sequence(Ty()) # Empty sequence
    else:
        ob = reduce(lambda a, b: a @ b, diagrams_list)
        ob = ob >> Sequence(ob.cod)

    if tag:
        tag_box = Box(tag, NODE, NODE)
        ob = ob >> tag_box
    return ob

def load_document(cursor):
    root = hif.step(cursor, "next")
    if root:
        return _incidences_to_diagram(root)
    return Id()

def load_stream(cursor):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    return reduce(lambda a, b: a @ b, diagrams, Id())
