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
    diagram = _incidences_to_diagram(node, 7)
    return diagram

def _incidences_to_diagram(node, index):
    """
    Takes an nx_yaml rooted bipartite graph
    and returns an equivalent string diagram
    """
    tag = (node.nodes[index+1].get("tag") or "")[1:]
    if node.nodes[index+1]["kind"] == "scalar":
        v = node.nodes[index+1]["value"]
        if not v:
            return Id()
        # if not tag:
        return Box(v, Ty(""), Ty(""))
        return Id(v)
        # return Bubble(Box(v, Ty(tag), Ty(tag)), drawing_name=tag)
    # TODO
    if node.nodes[index+1]["kind"] == "sequence":
        ob = Id(tag)
        # assert len(node.predecessors(edge)) == 1
        # index+1 = next(iter(node.predecessors(edge)))
        # assert len(node.out_edges(index+1)) == 1
        ktag = tag
        # TODO hyperedges create boxes from 
        for v in node[index+1]:
            vtag = (node.nodes[v+1].get("tag") or "")[1:]
            value = _incidences_to_diagram(node, v)
            # if ktag and vtag:
            #     value = Box(ktag, value.dom, value.dom) >> value
            # # elif ktag and not vtag:
            # #     value = Box(ktag, value.dom, value.dom) >> value
            # elif not ktag and vtag:
            #     value = value >> Box(vtag, value.cod, value.cod)
            value = Bubble(value, dom=ob.cod, drawing_name=vtag)
            ob = ob >> value
            ktag = vtag
        # if tag:
        #     return Bubble(ob, drawing_name=tag)
        return ob
    if node.nodes[index+1]["kind"] == "mapping":
        ob = Id()
        keys = Id()
        values = Id()
        for k, v in batched(node[index+1], 2):
            ktag = (node.nodes[k+1].get("tag") or "")[1:]
            vtag = (node.nodes[v+1].get("tag") or "")[1:]
            key = _incidences_to_diagram(node, k)
            value = _incidences_to_diagram(node, v)
            # if not tag and ktag and not vtag:
            #     key = key >> Box(ktag, key.cod, value.dom)
            #     # value = Id(value.cod)
            # elif not tag and not ktag and vtag:
            #     value = Box(vtag, key.cod, value.dom) >> value
            #     key = Id(key.dom)
            # elif not tag and ktag and vtag:
            #     key = key >> Box(ktag, key.cod, value.dom)
            #     value = Box(vtag, key.cod, value.dom) >> value
            # # elif tag and not ktag and not vtag:
            # elif tag and ktag and not vtag:
            #     key = key >> Box(ktag, key.cod, value.dom)
            # elif tag and not ktag and vtag:
            #     value = Box(vtag, key.cod, value.dom) >> value
            # elif tag and ktag and vtag:
            #     key_cod = key.cod
            #     key = key >> Box(ktag, key_cod, Ty(""))
            #     value = Box(vtag, Ty(""), value.dom) >> value
            if ktag:
                key = Bubble(key, drawing_name=ktag)
            if vtag:
                value = Bubble(value, drawing_name=vtag)
                # elif vtag and not value:
                #     kv = kv >> Box(vtag, kv.cod, kv.cod) >> value
            kv = glue_diagrams(key, value)
            ob @= kv
            keys @= key
            values @= value
        #     values = Id(values.cod)

        # TODO return cospan so callers
        # can glue or insert boxes
        #     return keys >> Box(tag, keys.cod, values.dom) >> values
        # if tag:
        #     return Bubble(ob, drawing_name=tag)
        return ob
        if values:
            if keys.cod == values.dom:
                return keys >> values
            return glue_diagrams(keys, values)
        return keys
