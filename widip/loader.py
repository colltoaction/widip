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
            ob @= doc
        return ob
    if kind == "document":
        (root, ) = node[index+1]
        return _incidences_to_diagram(node, root)
    if kind == "scalar":
        v = node.nodes[index+1]["value"]
        if not tag and not v:
            return Id("")
        if not tag:
            return Id(v)
        return Box(tag, Ty(v), Ty(v))
    if kind == "sequence":
        ob = Id()
        for v in node[index+1]:
            value = _incidences_to_diagram(node, v)
            if ob == Id():
                ob = value
            else:
                ob = ob >> Box("", ob.cod, value.dom) >> value
        return ob.bubble(dom="", cod="", drawing_name=tag)
    if kind == "mapping":
        ob = Id()
        keys = Id()
        values = Id()
        for k, v in batched(node[index+1], 2):
            key = _incidences_to_diagram(node, k)
            value = _incidences_to_diagram(node, v)
            kv = key >> Box("", key.cod, value.dom) >> value
            ob @= kv
            keys @= key
            values @= value
        if ob == Id():
            return ob
        return ob.bubble(dom="", cod="", drawing_name=tag)
