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
            dkind = hif_node(node, nxt_node)["kind"]
            dtag = (hif_node(node, nxt_node).get("tag") or "")[1:]
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
            return Box("G", Ty(tag) @ Ty(v), Ty() >> Ty(""))
            return Box("g", Ty(tag) @ Ty(v), Ty(""))
            return Box("G", Ty(tag) @ Ty(v), Ty() >> Ty(""))
        elif tag:
            return Box("g", Ty("io") @ Ty(tag), Ty("io")).curry(left=False)
        elif v:
            return Box("⌜−⌝", Ty(v), Ty() >> Ty(v))
            return Box("G", Ty(v), Ty() >> Ty(v))
            return Box("G", Ty(v), Ty("io") >> Ty("io"))
            return (Ty("io") @ Box("⌜−⌝", Ty(v), Ty() >> Ty(v))).curry(left=False)
        else:
            return Box("⌜−⌝", Ty(), Ty() >> Ty(v))
            return Box("⌜−⌝", Ty(v), Ty(v))
            return Box("G", Ty(), Ty() >> Ty(v))
            # return (Ty("io") @ Box("⌜−⌝", Ty(), Ty() >> Ty())).curry(left=False)
            # return Box("⌜−⌝", Ty(), P)
    if kind == "sequence":
        ob = Id()
        i = 0
        nxt = tuple(hif_node_incidences(node, index, key="next"))
        while True:
            if not nxt:
                break
            ((v_edge, _, _, _), ) = nxt
            ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")
            vkind = hif_node(node, v)["kind"]
            vtag = (hif_node(node, v).get("tag") or "")[1:]
            value = _incidences_to_diagram(node, v)
            if vkind == "scalar" and vtag:
                ob = ob >> Box(vtag, ob.cod, value.dom) >> value
            else:
                ob = glue_diagrams(ob, value)
            i += 1
            nxt = tuple(hif_node_incidences(node, v, key="forward"))
        if tag:
            ob = ob >> Box(tag, ob.cod, Ty(""))
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
            kkind = hif_node(node, k)["kind"]
            vkind = hif_node(node, v)["kind"]
            ktag = (hif_node(node, k).get("tag") or "")[1:]
            vtag = (hif_node(node, v).get("tag") or "")[1:]
            key = _incidences_to_diagram(node, k)
            value = _incidences_to_diagram(node, v)

            key_bases = Ty().tensor(*map(lambda x: getattr(x.inside[0], "base", Ty()), value.cod))
            value_exps = Ty().tensor(*map(lambda x: getattr(x.inside[0], "exponent", Ty()), key.cod))
            kv = key @ value
            bases = Ty().tensor(*map(lambda x: getattr(x.inside[0], "base", Ty()), key.cod + value.cod))
            exps = Ty().tensor(*map(lambda x: getattr(x.inside[0], "exponent", Ty()), key.cod + value.cod))
            kv = (value_exps @ (kv >> Box("(;)", kv.cod, value_exps >> key_bases))) >> Eval(value_exps >> key_bases)
            kv = kv.curry(len(kv.dom), left=False)

            if i==0:
                ob = kv
            else:
                ob = ob @ kv

            i += 1
            nxt = tuple(hif_node_incidences(node, v, key="forward"))
        if i > 1 or tag:
            bases = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))
            exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
            if tag:
                par_box = Box("(||)", ob.cod, exps >> bases)
                ob = ob >> par_box
                ob = exps @ ob >> Eval(par_box.cod)
                ob = Ty(tag) @ ob >> Box("G", Ty(tag) @ ob.cod, Ty() >> Ty(""))
            else:
                ob = (ob >> Box("(||)", ob.cod, exps >> bases))
                # ob = ob.cod.exponent @ ob >> Eval(ob.cod)
        return ob
