from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.markov import Id, Ty, Box, Hypergraph as DiscopyHypergraph

from .composing import glue_diagrams


# "io" type for general data flow
P = Ty("io")

def glue_diagrams(left, right):
    # Simplified glue: just compose in parallel.
    # Since blocks typically consume data and produce 'io',
    # and 'io' is not 'data', they don't chain sequentially.
    return left @ right

def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams.to_diagram()

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
        ob = DiscopyHypergraph.id()
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
            if ob == DiscopyHypergraph.id():
                ob = doc
            else:
                ob = glue_diagrams(ob, doc)

            nxt = tuple(hif_node_incidences(node, nxt_node, key="forward"))

        return ob
    if kind == "document":
        nxt = tuple(hif_node_incidences(node, index, key="next"))
        ob = DiscopyHypergraph.id()
        if nxt:
            ((root_e, _, _, _), ) = nxt
            ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
            ob = _incidences_to_diagram(node, root)
        return ob
    if kind == "scalar":
        v = hif_node(node, index)["value"]
        if tag and v:
            # G: tag @ v -> io
            return DiscopyHypergraph.from_box(Box("G", Ty(tag, v), P))
        elif tag:
            # G: tag -> io
            return DiscopyHypergraph.from_box(Box("G", Ty(tag), P))
        elif v:
            # ⌜−⌝: v -> io
            return DiscopyHypergraph.from_box(Box("⌜−⌝", Ty(v), P))
        else:
            # ⌜−⌝: empty -> io
            return DiscopyHypergraph.from_box(Box("⌜−⌝", Ty(), P))
    if kind == "sequence":
        ob = DiscopyHypergraph.id()
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
                ob = ob >> DiscopyHypergraph.from_box(Box("(;)", ob.cod, P))

            i += 1
            nxt = tuple(hif_node_incidences(node, v, key="forward"))
        if tag:
            # tag @ ob -> G -> P
            ev = Box("Eval", P @ P, P)
            ob = DiscopyHypergraph.id(P) @ ob >> DiscopyHypergraph.from_box(ev)

            box = Box("G", Ty(tag) @ ob.cod, P)
            ob = DiscopyHypergraph.id(Ty(tag)) @ ob >> DiscopyHypergraph.from_box(box)
        return ob
    if kind == "mapping":
        ob = DiscopyHypergraph.id()
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

        par_box = Box("(||)", ob.cod, P)
        ob = ob >> DiscopyHypergraph.from_box(par_box)

        if tag:
            ev = Box("Eval", P @ P, P)
            ob = ob @ DiscopyHypergraph.id(P) >> DiscopyHypergraph.from_box(ev)

            box = Box("G", Ty(tag) @ ob.cod, P)
            ob = DiscopyHypergraph.id(Ty(tag)) @ ob >> DiscopyHypergraph.from_box(box)
        return ob
