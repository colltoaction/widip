from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.closed import Id, Ty, Box, Eval

P = Ty() << Ty("")


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
        return Box("Ω", Ty(), Ty(v) << P) @ P \
            >> Eval(Ty(v) << P) \
            >> Box("e", Ty(v), Ty(v))
    if tag and v:
        return Box(tag, Ty(v), Ty() << Ty(""))
    elif tag:
        return Box(tag, Ty(), Ty() << Ty(""))
    elif v:
        return Box("⌜−⌝", Ty(v), Ty() << Ty(""))
    else:
        return Box("⌜−⌝", Ty(), Ty() << Ty(""))

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
    bases = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod[0::2]))
    exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod[1::2]))
    par_box = Box("(||)", ob.cod, exps << bases)
    ob = ob >> par_box
    if tag:
        ob = (ob @ bases>> Eval(exps << bases))
        ob = ob >> Box(tag, ob.cod, Ty("") << Ty(""))
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
