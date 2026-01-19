from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.closed import Id, Ty, Box, Eval

P = Ty() << Ty("")



def iter_linked_list(node, index):
    """
    Yields nodes in a linked list structure.
    First edge is 'next', subsequent are 'forward'.
    """
    edges = tuple(hif_node_incidences(node, index, key="next"))
    while edges:
        ((edge, _, _, _), ) = edges
        ((_, target, _, _), ) = hif_edge_incidences(node, edge, key="start")
        yield target
        edges = tuple(hif_node_incidences(node, target, key="forward"))


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
        return Box(tag, Ty(v), Ty(tag) >> Ty(tag))
    elif tag:
        return Box(tag, Ty(v), Ty(tag) >> Ty(tag))
    elif v:
        return Box("⌜−⌝", Ty(v), Ty() >> Ty(v))
    else:
        return Box("⌜−⌝", Ty(), Ty() >> Ty(v))

def load_mapping(node, index, tag):
    ob = Id()
    i = 0
    edges = tuple(hif_node_incidences(node, index, key="next"))
    while edges:
        ((k_edge, _, _, _), ) = edges
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
        edges = tuple(hif_node_incidences(node, v, key="forward"))
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
    for i, v in enumerate(iter_linked_list(node, index)):
        value = _incidences_to_diagram(node, v)
        if i==0:
            ob = value
        else:
            ob = ob @ value
            bases = ob.cod[0].inside[0].exponent
            exps = value.cod[0].inside[0].base
            ob = ob >> Box("(;)", ob.cod, bases >> exps)
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
    for nxt_node in iter_linked_list(node, index):
        doc = _incidences_to_diagram(node, nxt_node)
        if ob == Id():
            ob = doc
        else:
            ob = ob @ doc
    return ob
