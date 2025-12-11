from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import (
    hif_node, hif_node_incidences, hif_edge_incidences,
    HyperGraph as HIFHyperGraph
)

from discopy.closed import Ty as ClosedTy
from discopy.markov import Hypergraph, Box, Ty as MarkovTy

# Keep P using ClosedTy for internal type structure
P = ClosedTy() << ClosedTy("")

class Eval(Box):
    """
    Custom Eval box for Markov Hypergraphs that mimics discopy.closed.Eval behavior.
    """
    def __init__(self, x):
        """
        x: The type to evaluate. Expected to be a ClosedTy (Over or Under).
           If x is (a << b), then dom = (a << b) @ b, cod = a.
        """
        if hasattr(x, 'inside') and len(x.inside) > 0:
            obj = x.inside[0]
            if hasattr(obj, 'base') and hasattr(obj, 'exponent'):
                 self.base = obj.base
                 self.exponent = obj.exponent
                 dom = x @ self.exponent
                 cod = self.base
            else:
                 dom = x
                 cod = x
        else:
             dom = x
             cod = x

        super().__init__("Eval", dom, cod)


def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams

def incidences_to_diagram(node: HIFHyperGraph):
    # TODO properly skip stream and document start
    diagram = _incidences_to_diagram(node, 0)
    return diagram

def _incidences_to_diagram(node: HIFHyperGraph, index):
    """
    Takes an nx_yaml rooted bipartite graph
    and returns an equivalent string diagram (as a Hypergraph)
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
        ty_v = ClosedTy(v)
        ty_v_P = ty_v << P

        b1 = Hypergraph.from_box(Box("Ω", ClosedTy(), ty_v_P))
        p_wire = Hypergraph.id(P)

        step1 = b1 @ p_wire

        ev = Hypergraph.from_box(Eval(ty_v_P))

        b_e = Hypergraph.from_box(Box("e", ty_v, ty_v))

        return step1 >> ev >> b_e

    if tag and v:
        return Hypergraph.from_box(Box("G", ClosedTy(tag) @ ClosedTy(v), ClosedTy() << ClosedTy("")))
    elif tag:
        return Hypergraph.from_box(Box("G", ClosedTy(tag), ClosedTy() << ClosedTy("")))
    elif v:
        return Hypergraph.from_box(Box("⌜−⌝", ClosedTy(v), ClosedTy() << ClosedTy("")))
    else:
        return Hypergraph.from_box(Box("⌜−⌝", ClosedTy(), ClosedTy() << ClosedTy("")))

def load_mapping(node, index, tag):
    ob = Hypergraph.id(ClosedTy()) # Id()
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

    bases_objs = [x.inside[0].base for x in ob.cod[0::2]]
    exps_objs = [x.inside[0].exponent for x in ob.cod[1::2]]

    bases = ClosedTy(*bases_objs) if bases_objs else ClosedTy()
    exps = ClosedTy(*exps_objs) if exps_objs else ClosedTy()

    par_box = Hypergraph.from_box(Box("(||)", ob.cod, exps << bases))
    ob = ob >> par_box

    if tag:
        step1 = ob @ Hypergraph.id(bases)
        ev = Hypergraph.from_box(Eval(exps << bases))
        ob = step1 >> ev

        tag_wire = Hypergraph.id(ClosedTy(tag))
        step2 = tag_wire @ ob

        final_box = Hypergraph.from_box(Box("G", ClosedTy(tag) @ ob.cod, ClosedTy("") << ClosedTy("")))

        ob = step2 >> final_box

    return ob

def load_sequence(node, index, tag):
    ob = Hypergraph.id(ClosedTy())
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

            base_obj = ob.cod[0].inside[0].exponent
            exp_obj = value.cod[0].inside[0].base

            bases = ClosedTy(base_obj)
            exps = ClosedTy(exp_obj)

            seq_box = Hypergraph.from_box(Box("(;)", ob.cod, bases >> exps))
            ob = ob >> seq_box

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    if tag:
        bases_objs = [x.inside[0].exponent for x in ob.cod]
        exps_objs = [x.inside[0].base for x in ob.cod]

        bases = ClosedTy(*bases_objs) if bases_objs else ClosedTy()
        exps = ClosedTy(*exps_objs) if exps_objs else ClosedTy()

        step1 = Hypergraph.id(bases) @ ob
        ev = Hypergraph.from_box(Eval(bases >> exps))
        ob = step1 >> ev

        tag_wire = Hypergraph.id(ClosedTy(tag))
        step2 = tag_wire @ ob

        final_box = Hypergraph.from_box(Box("G", ClosedTy(tag) @ ob.cod, ClosedTy() >> ClosedTy(tag)))
        ob = step2 >> final_box

    return ob

def load_document(node, index):
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    ob = Hypergraph.id(ClosedTy())
    if nxt:
        ((root_e, _, _, _), ) = nxt
        ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
        ob = _incidences_to_diagram(node, root)
    return ob

def load_stream(node, index):
    ob = Hypergraph.id(ClosedTy())
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

        # If ob is empty (Id(Ty())), just take doc
        if len(ob.boxes) == 0 and len(ob.dom) == 0 and len(ob.cod) == 0:
             ob = doc
        else:
            if ob.cod == doc.dom:
                ob = ob >> doc
            else:
                ob = ob @ doc

        nxt = tuple(hif_node_incidences(node, nxt_node, key="forward"))
    return ob
