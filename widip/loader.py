from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.closed import Id, Ty, Box, Eval
P = Ty("io") >> Ty("io")

from .composing import glue_diagrams


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
    if kind == "stream":
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
                ob = glue_diagrams(ob, doc)

            nxt = tuple(hif_node_incidences(node, nxt_node, key="forward"))

        return ob
    if kind == "document":
        nxt = tuple(hif_node_incidences(node, index, key="next"))
        ob = Id()
        if nxt:
            ((root_e, _, _, _), ) = nxt
            ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
            ob = _incidences_to_diagram(node, root)
        return ob
    if kind == "scalar":
        v = hif_node(node, index)["value"]
        if tag and v:
            return Box("G", Ty(tag) @ Ty(v), Ty() >> Ty())
        elif tag:
            return Box("G", Ty(tag), Ty() >> Ty())
        elif v:
            return Box("⌜−⌝", Ty(v), Ty() >> Ty())
        else:
            return Box("⌜−⌝", Ty(), Ty() >> Ty())
    if kind == "sequence":
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
            ob = Box("G", Ty(tag), Ty() >> Ty()) @ ob
            ob = ob >> Box("(;)", ob.cod, Ty() >> Ty())
        return ob
    if kind == "mapping":
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
            bases = key.cod[0].inside[0].exponent
            exps = value.cod[0].inside[0].base
            kv = kv >> Box("(;)", kv.cod, bases >> exps)

            if i==0:
                ob = kv
            else:
                ob = ob @ kv

            i += 1
            nxt = tuple(hif_node_incidences(node, v, key="forward"))
        bases = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
        exps = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))
        par_box = Box("(||)", ob.cod, bases >> exps)
        ob = ob >> par_box
        if tag:
            ob = Box("G", Ty(tag), bases >> exps) @ ob
            ob = ob >> Box("(;)", ob.cod, bases >> exps)
        return ob
