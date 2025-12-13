from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.frobenius import Id, Ty, Box, Swap

S = Ty("")


def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams

def incidences_to_diagram(node: HyperGraph):
    diagram = _incidences_to_diagram(node, 0)
    return diagram

def _incidences_to_diagram(node: HyperGraph, index):
    tag = (hif_node(node, index).get("tag") or "")[1:]
    kind = hif_node(node, index)["kind"]

    match kind:

        case "stream":
            ob = load_stream(node, index)
        case "document":
            ob = load_document(node, index)
        case "scalar":
            ob = load_scalar(node, index, tag)
        case "sequence":
            ob = load_sequence(node, index, tag)
        case "mapping":
            ob = load_mapping(node, index, tag)
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    return ob


def load_scalar(node, index, tag):
    v = hif_node(node, index)["value"]

    if tag == "fix" and v:
         return Box("Ω", Ty(), S) >> Box("e", S, S)

    if not tag and not v:
        # Return a Box that produces the identity function
        return Box("id", Ty(), S)

    dom = Ty()
    # Note: tag is now used as name, so we don't add it to domain
    # If explicit value v exists, we add it to domain
    if v:
        dom = dom @ Ty(v)

    name = tag if tag else ("G" if tag else "⌜−⌝") # If tag, use tag. Else if v?
    # Original logic: if tag -> G. if v -> ⌜−⌝.
    # If we want generic tags to be box names:
    if tag:
        name = tag
    else:
        name = "⌜−⌝"

    return Box(name, dom, S)

def load_mapping(node, index, tag):
    ob = Id()
    i = 0
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt:
            break
        ((k_edge, _, _, _), ) = nxt
        ((_, k, _, _), ) = hif_edge_incidences(node, k_edge, key="start")
        ((v_edge, _, _, _), ) = hif_node_incidences(node, k, key="forward")
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")

        key = _incidences_to_diagram(node, k)
        value = _incidences_to_diagram(node, v)

        kv = key @ value

        if i==0:
            ob = kv
        else:
            ob = ob @ kv

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    if i == 0:
        # Empty mapping acts as identity source
        ob = Box("id", Ty(), S)
    else:
        par_box = Box("(||)", ob.cod, S)
        ob = ob >> par_box

    if tag:
        # Use tag as name, consume output of ob
        ob = ob >> Box(tag, S, S)

    return ob

def load_sequence(node, index, tag):
    ob = Id()
    i = 0
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt:
            break
        ((v_edge, _, _, _), ) = nxt
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")
        value = _incidences_to_diagram(node, v)
        if i==0:
            ob = value
        else:
            ob = ob @ value >> Box("(;)", S @ S, S)

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    if tag:
        ob = ob >> Box(tag, S, S)

    return ob

def load_document(node, index):
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    ob = Id()
    if nxt:
        ((root_e, _, _, _), ) = nxt
        ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
        ob = _incidences_to_diagram(node, root)
    return ob

def load_stream(node, index):
    ob = Id()
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt:
            break
        ((nxt_edge, _, _, _), ) = nxt
        starts = tuple(hif_edge_incidences(node, nxt_edge, key="start"))
        if not starts:
            break
        ((_, nxt_node, _, _), ) = starts
        doc = _incidences_to_diagram(node, nxt_node)
        if ob == Id():
            ob = doc
        else:
            ob = ob @ doc

        nxt = tuple(hif_node_incidences(node, nxt_node, key="forward"))
    return ob
