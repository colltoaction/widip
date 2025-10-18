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
        if not v and tag:
            ob = Id("")
        elif not v:
            ob = Id()
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
            if value == Id() and vtag:
                ob = ob >> Box(vtag, ob.cod, Ty())
            elif value != Id() and vtag:
                ob = glue_diagrams(ob, Box(vtag, value.dom, value.cod))
            elif value != Id():
                ob = glue_diagrams(ob, value)
        if ob != Id(ob.dom):
            obub = Bubble(ob, ob.dom, ob.cod, drawing_name=kind)
        else:
            obub = ob
        return obub
    if kind == "mapping":
        ob = Id()
        keys = Id()
        values = Id()
        i = 0
        for k, v in batched(node[index+1], 2):
            ktag = (node.nodes[k+1].get("tag") or "")[1:]
            vtag = (node.nodes[v+1].get("tag") or "")[1:]
            key = _incidences_to_diagram(node, k)
            value = _incidences_to_diagram(node, v)
            if key != Id() and ktag:
                kv = Box(ktag, key.dom, value.dom)
            elif key != Id():
                kbub = Bubble(key, key.dom, key.cod, drawing_name=kind)
                if kbub.is_id_on_objects:
                    kv = kbub.arg
                else:
                    kv = kbub
            elif ktag:
                kv = Box(ktag, Ty(), value.dom)
            else:
                kv = key
            if value != Id() and vtag:
                kv = kv >> Box(vtag, kv.cod, value.cod)
            elif value != Id():
                vbub = Bubble(value, kv.cod, value.cod, drawing_name=kind)
                if vbub.is_id_on_objects:
                    kv = kv >> vbub.arg
                else:
                    kv = kv >> vbub
            ob @= kv
            keys @= key
            values @= value
            i += 1
        if i > 1 and ob != Id(ob.dom):
            obub = Bubble(ob, ob.dom, ob.cod, drawing_name=kind)
        else:
            obub = ob
        return obub
