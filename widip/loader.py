from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.frobenius import Id, Ty, Box, Category

S = Ty("s")


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
    if tag == "fix" and v:
        # TODO: Implement fixpoint logic for Frobenius if needed
        raise NotImplementedError("fix tag not implemented for Frobenius")

    if tag and v:
        # Literal input (v) -> Effect (tag)
        # v: Ty() -> S (triangle down)
        # tag: S -> Ty()

        lit = Box(v, Ty(), S, drawing_name=v, shape="triangle_down", color="red")
        eff = Box(tag, S, Ty())
        return lit >> eff

    elif tag:
        # Just a tag, assumed to be a generator Ty() -> S for now
        return Box(tag, Ty(), S)

    elif v:
        # Just a value: Ty() -> S
        return Box(v, Ty(), S, drawing_name=v, shape="triangle_down", color="red")
    else:
        # Empty scalar
        return Box("⌜−⌝", Ty(), S)

def load_mapping(node, index, tag):
    ob = Id(Ty())
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

        # Mapping key: value -> key @ value in parallel
        kv = key @ value

        if i==0:
            ob = kv
        else:
            ob = ob @ kv

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    # If tag is present, apply it to the mapping result?
    # Previous code did: Ty(tag) @ ob >> Box("G", ...)
    if tag:
        # For now, just return the mapping.
        # Implementing full logic requires knowing semantics of tagged mapping.
        # Assuming it processes the mapping.
        pass

    return ob

def load_sequence(node, index, tag):
    ob = Id(Ty())
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
            # Sequential composition
            # If ob is Id(Ty()), it acts as identity.
            # If ob is not Id, we compose.
            # Note: Id(Ty()) >> value works if value.dom == Ty()
            ob = ob >> value

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    if tag:
        # Previous code handled tag.
        pass

    return ob

def load_document(node, index):
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    ob = Id(Ty())
    if nxt:
        ((root_e, _, _, _), ) = nxt
        ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
        ob = _incidences_to_diagram(node, root)
    return ob

def load_stream(node, index):
    ob = Id(Ty())
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
        if ob == Id(Ty()):
            ob = doc
        else:
            ob = ob @ doc

        nxt = tuple(hif_node_incidences(node, nxt_node, key="forward"))
    return ob
