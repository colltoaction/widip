from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.frobenius import Id, Ty, Box, Spider

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
            elif dkind == "scalar" and dtag:
                ob = ob >> Box(dtag, ob.cod, doc.dom) >> doc
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
            rkind = hif_node(node, root)["kind"]
            rtag = (hif_node(node, root).get("tag") or "")[1:]
            if rkind == "scalar" and rtag:
                rval = hif_node(node, root)["value"]
                ob = Box(rtag, Ty(rval), Ty(""))
            else:
                ob = _incidences_to_diagram(node, root)
        return ob
    if kind == "scalar":
        v = hif_node(node, index)["value"]
        return Id(v)
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
        if i > 1 and ob != Id(ob.dom):
            ob = ob.bubble(dom=ob.dom, cod=ob.cod, drawing_name=kind)
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
            if kkind == "scalar" and vkind == "scalar" and not ktag and not vtag:
                kval = hif_node(node, k)["value"]
                vval = hif_node(node, v)["value"]
                kv = Box(kval, Ty(""), Ty("")) >> \
                     (Box(vval, Ty(""), Ty("")) if vval else Id(""))
            elif kkind == "scalar" and vkind == "scalar" and ktag and vtag:
                kbox = Box(ktag, key.dom, value.dom)
                vbox = Box(vtag, value.dom, Ty(""))
                kv = kbox >> vbox
            elif kkind == "scalar" and vkind == "scalar" and ktag and not vtag:
                kval = hif_node(node, k)["value"]
                vval = hif_node(node, v)["value"]
                kv = (key >> Box(ktag, key.cod, Ty(""))) >> \
                     (Box(vval, Ty(""), Ty("")) if vval else Id(""))
            elif vkind == "scalar" and not ktag and vtag:
                vval = hif_node(node, v)["value"]
                kv = (key @ Spider(0, 1, Ty(vval))) >> \
                      Box(vtag, key.cod @ Ty(vval), Ty(""))
            elif kkind == "scalar" and ktag and value == Id(""):
                kv = key >> Box(ktag, key.cod, Ty(""))
            elif ktag:
                kv = key >> Box(ktag, key.cod, value.dom) >> value
            elif vkind == "scalar" and vtag:
                kv = key >> Box(vtag, key.cod, value.dom) >> value
            elif value == Id(""):
                kv = key
            else:
                kv = glue_diagrams(key, value)

            ob @= kv
            i += 1
            nxt = tuple(hif_node_incidences(node, v, key="forward"))
        # if tag:
        #     ob = ob >> Box(tag, ob.cod, Ty(""))
        if i > 1 and ob != Id(ob.dom):
            ob = ob.bubble(dom=ob.dom, cod=ob.cod, drawing_name=kind)
        return ob
