from nx_hif.hif import HyperGraph, hif_node, hif_node_incidences, hif_edge_incidences
from discopy.markov import Box, Ty, Id, Diagram, Functor, Copy, Discard, Trace

def hif_to_markov(node: HyperGraph):
    return _hif_to_markov(node, 0)

def _hif_to_markov(node: HyperGraph, index):
    tag = (hif_node(node, index).get("tag") or "")[1:]
    kind = hif_node(node, index)["kind"]

    match kind:
        case "stream":
            return load_stream(node, index)
        case "document":
            return load_document(node, index)
        case "scalar":
            return load_scalar(node, index, tag)
        case "sequence":
            return load_sequence(node, index, tag)
        case "mapping":
            return load_mapping(node, index, tag)
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

def load_scalar(node, index, tag):
    v = hif_node(node, index)["value"]

    if tag == "fix":
        name = "fix"
        dom = Ty()
        cod = Ty(str(v) if v else "x")
        return Box(name, dom, cod)

    return Box(str(v) if v is not None else (tag or "unknown"), Ty(), Ty("node"))

def load_mapping(node, index, tag):
    children = []
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt: break
        ((k_edge, _, _, _), ) = nxt
        ((_, k, _, _), ) = hif_edge_incidences(node, k_edge, key="start")
        ((v_edge, _, _, _), ) = hif_node_incidences(node, k, key="forward")
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")

        key_diag = _hif_to_markov(node, k)
        val_diag = _hif_to_markov(node, v)
        children.append(key_diag @ val_diag)

        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    if not children:
        ob = Id()
    else:
        ob = children[0]
        for child in children[1:]:
            ob = ob @ child

    if tag:
        ob = ob >> Box(tag, ob.cod, Ty("node"))

    return ob

def load_sequence(node, index, tag):
    children = []
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt: break
        ((v_edge, _, _, _), ) = nxt
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")
        children.append(_hif_to_markov(node, v))
        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    if not children:
        ob = Id()
    else:
        ob = children[0]
        for child in children[1:]:
            ob = ob @ child

    if tag:
        ob = ob >> Box(tag, ob.cod, Ty("node"))

    return ob

def load_document(node, index):
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    if nxt:
        ((root_e, _, _, _), ) = nxt
        ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
        return _hif_to_markov(node, root)
    return Id()

def load_stream(node, index):
    ob = Id()
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt: break
        ((nxt_edge, _, _, _), ) = nxt
        starts = tuple(hif_edge_incidences(node, nxt_edge, key="start"))
        if not starts: break
        ((_, nxt_node, _, _), ) = starts

        doc = _hif_to_markov(node, nxt_node)
        if ob == Id():
            ob = doc
        else:
            ob = glue_diagrams(ob, doc)

        nxt = tuple(hif_node_incidences(node, nxt_node, key="forward"))
    return ob

def glue_diagrams(left, right):
    if left.cod == right.dom:
        return left >> right
    return left @ right
