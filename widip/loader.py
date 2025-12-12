from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.frobenius import Id, Ty, Box, Spider

S = Ty("String")


def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams

def incidences_to_diagram(node: HyperGraph):
    # TODO properly skip stream and document start
    diagram = _incidences_to_diagram(node, 0)
    return diagram

def _incidences_to_diagram(node: HyperGraph, index):
    """
    Takes an nx_yaml rooted bipartite graph
    and returns an equivalent string diagram
    """
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

    if tag and v:
        # Merge tag and value into one command box to preserve flow
        # e.g. "wc -c"
        return Box(f"command: {tag} {v}", S, S)
    elif tag:
        return Box(f"command: {tag}", S, S)
    elif v:
        return Box(f"Value: {v}", S, S)
    else:
        # Null value. Identity?
        return Id(S)

def load_mapping(node, index, tag):
    items = []
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while nxt:
        ((k_edge, _, _, _), ) = nxt
        ((_, k, _, _), ) = hif_edge_incidences(node, k_edge, key="start")
        ((v_edge, _, _, _), ) = hif_node_incidences(node, k, key="forward")
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")

        key_d = _incidences_to_diagram(node, k)
        val_d = _incidences_to_diagram(node, v)

        items.append(key_d >> val_d)

        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    n = len(items)
    if n == 0:
        return Box("Discard", S, Ty())

    copy_box = Spider(1, n, S)

    branches = Id(Ty())
    for b in items:
        if branches == Id(Ty()):
            branches = b
        else:
            branches = branches @ b

    ob = copy_box >> branches

    if tag:
        ob = ob >> Box(f"command: {tag}", ob.cod, S)

    return ob

def load_sequence(node, index, tag):
    ob = Id(S)
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    first = True
    while nxt:
        ((v_edge, _, _, _), ) = nxt
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")
        val_d = _incidences_to_diagram(node, v)

        if first:
            ob = val_d
            first = False
        else:
            ob = ob >> val_d

        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    if tag:
        ob = ob >> Box(f"command: {tag}", S, S)
    return ob

def load_document(node, index):
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    ob = Id(S)
    if nxt:
        ((root_e, _, _, _), ) = nxt
        ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
        ob = _incidences_to_diagram(node, root)

    # Root document starts with Ty().
    return Box("Value: ", Ty(), S) >> ob

def load_stream(node, index):
    ob = Id(S)
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while nxt:
        ((nxt_edge, _, _, _), ) = nxt
        starts = tuple(hif_edge_incidences(node, nxt_edge, key="start"))
        if not starts:
            break
        ((_, nxt_node, _, _), ) = starts
        doc = _incidences_to_diagram(node, nxt_node)

        if ob == Id(S):
            ob = doc
        else:
            ob = ob @ doc

        nxt = tuple(hif_node_incidences(node, nxt_node, key="forward"))
    return ob
