from nx_yaml import NxSafeLoader, NxSafeDumper
from yaml import compose_all as yaml_compose_all, serialize as yaml_serialize

from discopy.frobenius import Hypergraph as H, Id, Ob, Ty, Box, Spider

from .composing import glue_diagrams


def repl_read(stream):
    inc_graphs = yaml_compose_all(stream, Loader=NxSafeLoader)
    diagrams = Id().tensor(*(
        incidences_to_diagram(g.graph) for g in inc_graphs
    ))
    return diagrams

def repl_print(diagram):
    return yaml_serialize(diagram, Dumper=NxSafeDumper)

def incidences_to_diagram(node):
    diagram = _incidences_to_diagram(node, 0)
    tag = (node.nodes[0].get("tag") or "")[1:]
    if tag:
        diagram = diagram >> Box(tag, diagram.cod, diagram.cod)
    return diagram

def _incidences_to_diagram(node, edge):
    """
    Takes an nx_yaml rooted bipartite graph
    and returns an equivalent string diagram
    """
    root = node.nodes[edge]
    assert root["bipartite"] == 0
    root_neighbors = node[edge]
    assert all(node.nodes[n]["bipartite"] == 1 for n in root_neighbors)
    tag = (root.get("tag") or "")[1:]
    if root["kind"] == "scalar":
        v = root["value"]
        return Id(v)
    if root["kind"] == "sequence":
        ob = Id()
        assert len(node.out_edges(edge)) == 1
        content_node = next(iter(root_neighbors))
        assert len(node.in_edges(content_node)) == 1
        ktag = tag
        for v in node[content_node]:
            vtag = (node.nodes[v].get("tag") or "")[1:]
            value = _incidences_to_diagram(node, v)
            if ktag and vtag:
                value = Box(ktag, value.dom, value.dom) >> value
            # elif ktag and not vtag:
            #     value = Box(ktag, value.dom, value.dom) >> value
            elif not ktag and vtag:
                value = value >> Box(vtag, value.cod, value.cod)
            ob = glue_diagrams(ob, value)
            ktag = vtag
        return ob
    if root["kind"] == "mapping":
        keys = Id()
        values = Id()
        for pair_node in root_neighbors:
            pair_edges = node.edges(pair_node)
            assert len(node.in_edges(pair_node)) == 1
            assert len(node.out_edges(pair_node)) == 2
            pair_edges = iter(pair_edges)
            _, k = next(pair_edges)
            _, v = next(pair_edges)
            ktag = (node.nodes[k].get("tag") or "")[1:]
            vtag = (node.nodes[v].get("tag") or "")[1:]
            key = _incidences_to_diagram(node, k)
            value = _incidences_to_diagram(node, v)
            # if not value:
            #     value = Id(key.cod)

            if not tag and ktag and not vtag:
                key = key >> Box(ktag, key.cod, value.dom)
                # value = Id(value.cod)
            elif not tag and not ktag and vtag:
                value = Box(vtag, key.cod, value.dom) >> value
                key = Id(key.dom)
            elif not tag and ktag and vtag:
                key = key >> Box(ktag, key.cod, value.dom)
                value = Box(vtag, key.cod, value.dom) >> value
            # elif tag and not ktag and not vtag:
            elif tag and ktag and not vtag:
                key = key >> Box(ktag, key.cod, value.dom)
            elif tag and not ktag and vtag:
                value = Box(vtag, key.cod, value.dom) >> value
            elif tag and ktag and vtag:
                key_cod = key.cod
                key = key >> Box(ktag, key_cod, Ty(""))
                value = Box(vtag, Ty(""), value.dom) >> value
            keys @= key
            values @= value
        #     values = Id(values.cod)

        # TODO return cospan so callers
        # can glue or insert boxes
        # if tag:
        #     return keys >> Box(tag, keys.cod, values.dom) >> values
        if values:
            if keys.cod == values.dom:
                return keys >> values
            return glue_diagrams(keys, values)
        return keys
