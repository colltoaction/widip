from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.closed import Eval

from .lang import Box, Id, Ty


P = Ty("io") >> Ty("io")


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
    """Figure 2.3: If g = {G}, then g ◦ (s × id) = {Gs} uses G but g ◦ (id × t) = {H} does not."""
    v = hif_node(node, index)["value"]
    X = Ty(tag) if tag else Ty()
    A = Ty(v) if v else Ty()
    if X == Ty() and A != Ty():
        return Id(A >> Ty()).curry(1, left=True)
    if X != Ty() and A == Ty():
        return Id(X >> Ty()).curry(1, left=False)
    return Id(X @ A >> Ty()).curry(1, left=True)

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

        exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, key.cod))
        bases = Ty().tensor(*map(lambda x: x.inside[0].base, value.cod))
        kv_box = Box("(;)", key.cod @ value.cod, exps >> bases)
        kv = key @ value >> kv_box

        if i==0:
            ob = kv
        else:
            ob = ob @ kv

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))
    exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
    bases = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))
    par_box = Box("(||)", ob.cod, exps >> bases)
    ob = ob >> par_box
    if tag:
        ob = (ob @ exps >> Eval(exps >> bases))
        box = Box(tag, ob.cod, Ty(tag) >> Ty(tag))
        ob = ob >> box
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
            ob = ob @ value
            bases = ob.cod[0].inside[0].exponent
            exps = value.cod[0].inside[0].base
            ob = ob >> Box("(;)", ob.cod, bases >> exps)

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))
    if tag:
        bases = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
        exps = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))
        ob = (bases @ ob >> Eval(bases >> exps))
        ob = ob >> Box(tag, ob.cod, Ty() >> Ty(tag))
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
