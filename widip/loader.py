from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all

from discopy.frobenius import Hypergraph as H, Id, Ob, Ty, Box, Spider, Bubble, Diagram

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
    # TODO bubbles always have "Bubble" box name
    tag = (node.nodes[index+1].get("tag") or "")[1:]
    kind = node.nodes[index+1]["kind"]
    if kind == "stream":
        ob = Id()
        for v in node[index+1]:
            doc = _incidences_to_diagram(node, v)
            # TODO documents are sequential
            ob @= doc
        if ob != Id(ob.dom):
            obub = ob.bubble(dom=ob.dom, cod=ob.cod, drawing_name=tag or kind)
        else:
            obub = ob
        return obub
    if kind == "document":
        (root, ) = node[index+1]
        ob = _incidences_to_diagram(node, root)
        obub = ob.bubble(dom=ob.dom, cod=ob.cod, drawing_name=tag or kind)
        return obub
    if kind == "scalar":
        v = node.nodes[index+1]["value"]
        if not v:
            ob = Id("")
        else:
            ob = Id(v)
        return ob
    if kind == "sequence":
        ob = Id()
        i = 0
        for v in node[index+1]:
            vtag = (node.nodes[v+1].get("tag") or "")[1:]
            value = _incidences_to_diagram(node, v)
            if i < 1:
                if vtag:
                    ob = Box(vtag, Ty(""), value.dom) >> value
                else:
                    ob = value
            else:
                if vtag:
                    if value == Id(""):
                        ob = ob >> Box(vtag, ob.cod, Ty(""))
                    else:
                        value = Box(vtag, Ty(""), value.dom) >> value
                        ob = glue_diagrams(ob, value)
                elif value != Id():
                    ob = glue_diagrams(ob, value)
            i += 1
        if tag:
            ob = ob >> Box(tag, ob.cod, Ty(""))
        if i > 1:
            ob = ob.bubble(dom=ob.dom, cod=ob.cod, drawing_name=kind)
        return ob
    if kind == "mapping":
        ob = Id()
        i = 0
        for k, v in batched(node[index+1], 2):
            kkind = node.nodes[k+1]["kind"]
            vkind = node.nodes[v+1]["kind"]
            ktag = (node.nodes[k+1].get("tag") or "")[1:]
            vtag = (node.nodes[v+1].get("tag") or "")[1:]
            key = _incidences_to_diagram(node, k)
            value = _incidences_to_diagram(node, v)
            if kkind == "scalar" and vkind == "scalar" and ktag and vtag:
                kv = key >> Box(ktag, key.cod, Ty("")) >> \
                    Box(vtag, Ty(""), value.dom) >> value
            elif kkind == "scalar" and ktag and value == Id(""):
                kv = key >> Box(ktag, key.cod, Ty(""))
            elif kkind == "scalar" and ktag:
                kv = key >> Box(ktag, key.cod, value.dom) >> value
            elif vkind == "scalar" and vtag:
                kv = key >> Box(vtag, key.cod, value.dom) >> value
            else:
                kv = glue_diagrams(key, value)

            ob @= kv
            i += 1
        if tag:
            ob = ob >> Box(tag, ob.cod, Ty(""))
        if i > 1:
            ob = ob.bubble(dom=ob.dom, cod=ob.cod, drawing_name=kind)
        return ob
