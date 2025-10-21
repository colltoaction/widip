from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all

from discopy.frobenius import Hypergraph as H, Id, Ob, Ty, Box, Spider, Bubble

from .composing import glue_diagrams


def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams

def repl_print(diagram):
    return nx_serialize_all(diagram)

def incidences_to_diagram(node):
    # TODO properly skip stream and document start
    diagram = _incidences_to_diagram(node, 0)
    return diagram

def _incidences_to_diagram(node, index):
    """
    Takes an nx_yaml rooted bipartite graph
    and returns an equivalent string diagram
    """
    tag = (node.nodes[index+1].get("tag") or "")[1:]
    kind = node.nodes[index+1]["kind"]
    if kind == "stream":
        ob = Id()
        for v in node[index+1]:
            doc = _incidences_to_diagram(node, v)
            # TODO documents are sequential
            ob @= doc
        if ob != Id(ob.dom):
            obub = Bubble(ob, ob.dom, ob.cod, drawing_name=tag or kind)
        else:
            obub = ob
        return obub
    if kind == "document":
        (root, ) = node[index+1]
        ob = _incidences_to_diagram(node, root)
        obub = Bubble(ob, ob.dom, ob.cod, drawing_name=tag or kind)
        return obub
    if kind == "scalar":
        v = node.nodes[index+1]["value"]
        if not v and tag:
            ob = Box(tag, Ty(""), Ty(""))
        elif not v:
            ob = Id("")
        else:
            ob = Id(v)
        return ob
    if kind == "sequence":
        ob = Id()
        for v in node[index+1]:
            vtag = (node.nodes[v+1].get("tag") or "")[1:]
            value = _incidences_to_diagram(node, v)
            if ob == Id():
                ob = Id(value.dom)
            if vtag:
                if value == Id():
                    ob = ob >> Box(vtag, ob.cod, Ty())
                else:
                    ob = glue_diagrams(ob, Box(vtag, value.dom, value.cod))
            elif value != Id():
                ob = glue_diagrams(ob, value)
        return ob
    if kind == "mapping":
        ob = Id()
        keys = Id()
        values = Id()
        for k, v in batched(node[index+1], 2):
            kkind = node.nodes[k+1]["kind"]
            vkind = node.nodes[v+1]["kind"]
            ktag = (node.nodes[k+1].get("tag") or "")[1:]
            vtag = (node.nodes[v+1].get("tag") or "")[1:]
            key = _incidences_to_diagram(node, k)
            value = _incidences_to_diagram(node, v)
            if kkind == "scalar" and vkind == "scalar" and tag and not ktag and not vtag and key != Id(key.dom):
                kv = Box(tag, key.dom, value.dom)
            elif kkind != "scalar" and key != Id(key.dom):
                kbub = Bubble(key, key.dom, key.cod, drawing_name=ktag or kkind)
                kv = kbub
            elif ktag:
                kv = Box(ktag, key.dom, value.dom)
            else:
                kv = key
            if value == Id(value.dom) and vtag:
                kv = glue_diagrams(kv, Box(vtag, value.dom, value.dom))
            elif value != Id(value.dom) or vtag:
                kv = kv >> Box(vtag, kv.cod, value.cod)
            elif value != Id(""):
                vbub = Bubble(value, kv.cod, value.cod, drawing_name=vtag)
                if vbub.is_id_on_objects:
                    kv = kv >> vbub.arg
                else:
                    kv = kv >> vbub
            ob @= kv
            keys @= key
            values @= value
        return ob
