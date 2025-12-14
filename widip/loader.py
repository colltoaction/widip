from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.symmetric import Ty, Box, Diagram, Category
from discopy.hypergraph import Hypergraph

class WidipHypergraph(Hypergraph):
    """
    Hypergraph for Widip.
    Uses symmetric types (strings).
    """
    category = Category
    pass

IO = Ty("io")


def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams

def incidences_to_diagram(node: WidipHypergraph):
    # TODO properly skip stream and document start
    diagram = _incidences_to_diagram(node, 0)
    return diagram

def _incidences_to_diagram(node: WidipHypergraph, index):
    """
    Takes an nx_yaml rooted bipartite graph
    and returns an equivalent hypergraph
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
    # We use the domain of the box to store the scalar value if it exists.
    # The codomain is IO to indicate it produces an output in the flow.
    # "fix" tag seems to be special, originally used Eval.
    # For now, map to a box.
    if tag == "fix" and v:
        # e = Box(v, IO, IO)
        # copy = Spider(1, 2, IO)
        # trace(e >> copy)
        e = WidipHypergraph.from_box(Box(v, IO, IO))
        copy = WidipHypergraph.spiders(1, 2, IO)
        return (e >> copy).trace()

    if tag and v:
        return WidipHypergraph.from_box(Box("G", Ty(tag) @ Ty(v), IO))
    elif tag:
        return WidipHypergraph.from_box(Box("G", Ty(tag), IO))
    elif v:
        # Store v in domain type as in original loader
        return WidipHypergraph.from_box(Box("⌜−⌝", Ty(v), IO))
    else:
        return WidipHypergraph.from_box(Box("⌜−⌝", Ty(), IO))

def load_mapping(node, index, tag):
    ob = None
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

        if ob is None:
            ob = kv
        else:
            ob = ob @ kv

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    if ob is None:
        ob = WidipHypergraph.id(Ty())

    # Map box takes all inputs and produces IO
    par_box = WidipHypergraph.from_box(Box("(||)", ob.cod, IO))
    ob = ob >> par_box

    if tag:
        # tag box
        # Original: (ob @ id >> eval) ...
        # Here we just chain.
        # Box G takes Ty(tag) and the output of the map.
        ob = WidipHypergraph.id(Ty(tag)) @ ob >> WidipHypergraph.from_box(Box("G", Ty(tag) @ ob.cod, IO))
    return ob

def load_sequence(node, index, tag):
    ob = None
    i = 0
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt:
            break
        ((v_edge, _, _, _), ) = nxt
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")
        value = _incidences_to_diagram(node, v)
        if ob is None:
            ob = value
        else:
            ob = ob @ value
            # Original inserted (;) box between elements?
            # "ob = ob @ value ... ob = ob >> Box((;), ...)"
            # It seems it was combining cumulative result with new value?
            # Let's just collect all values and then apply (;) at the end?
            # Wait, the original code loop:
            # ob = value (first)
            # loop:
            #   ob = ob @ value
            #   ob = ob >> Box("(;)", ...)
            # This looks like fold?
            # But the box signature was ob.cod (which is prev_cod @ new_cod) -> bases >> exps.
            # bases=prev, exps=new.
            # So it was reducing pair to single output.

            # Here we can do the same structure.
            # ob has codomain IO (from previous step).
            # value has codomain IO.
            # ob @ value has codomain IO @ IO.
            # (;) box takes IO @ IO -> IO.
            ob = ob >> WidipHypergraph.from_box(Box("(;)", ob.cod, IO))

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    if ob is None:
        ob = WidipHypergraph.id(Ty())

    if tag:
        ob = WidipHypergraph.id(Ty(tag)) @ ob >> WidipHypergraph.from_box(Box("G", Ty(tag) @ ob.cod, IO))
    return ob

def load_document(node, index):
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    ob = WidipHypergraph.id(Ty())
    if nxt:
        ((root_e, _, _, _), ) = nxt
        ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
        ob = _incidences_to_diagram(node, root)
    return ob

def load_stream(node, index):
    ob = None
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
        if ob is None:
            ob = doc
        else:
            ob = ob @ doc

        nxt = tuple(hif_node_incidences(node, nxt_node, key="forward"))

    if ob is None:
        ob = WidipHypergraph.id(Ty())
    return ob
