from nx_yaml import nx_compose_all
from nx_hif.hif import *
from discopy.closed import Id, Ty, Box, Eval

P = Ty() << Ty("")

def iter_linked_list(node, index):
    edges = tuple(hif_node_incidences(node, index, key="next"))
    while edges:
        ((edge, _, _, _), ) = edges
        ((_, target, _, _), ) = hif_edge_incidences(node, edge, key="start")
        yield target
        edges = tuple(hif_node_incidences(node, target, key="forward"))

def repl_read(stream):
    return _load_node(nx_compose_all(stream), 0)

def _load_node(node, index, tag=None):
    if tag is None:
        tag = (hif_node(node, index).get("tag") or "")[1:]
    kind = hif_node(node, index)["kind"]
    loaders = {"stream": _load_stream, "document": _load_document, 
               "scalar": _load_scalar, "sequence": _load_sequence, "mapping": _load_mapping}
    if kind not in loaders:
        raise Exception(f"Unknown kind: {kind}")
    return loaders[kind](node, index, tag)

def _load_scalar(node, index, tag):
    v = hif_node(node, index)["value"]
    if tag == "fix" and v:
        return Box("Ω", Ty(), Ty(v) << P) @ P >> Eval(Ty(v) << P) >> Box("e", Ty(v), Ty(v))
    if tag and v: return Box(tag, Ty(v), Ty(tag) >> Ty(tag))
    if tag: return Box(tag, Ty(v) if v else Ty(), Ty(tag) >> Ty(tag))
    if v: return Box("⌜−⌝", Ty(v), Ty() >> Ty(v))
    return Box("⌜−⌝", Ty(), Ty() >> Ty(v))

def _load_mapping(node, index, tag):
    ob, edges = Id(), tuple(hif_node_incidences(node, index, key="next"))
    while edges:
        ((k_edge, _, _, _), ) = edges
        ((_, k, _, _), ) = hif_edge_incidences(node, k_edge, key="start")
        ((v_edge, _, _, _), ) = hif_node_incidences(node, k, key="forward")
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")
        key, value = _load_node(node, k, None), _load_node(node, v, None)
        exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, key.cod))
        bases = Ty().tensor(*map(lambda x: x.inside[0].base, value.cod))
        kv = key @ value >> Box("(;)", key.cod @ value.cod, exps >> bases)
        ob = kv if ob == Id() else ob @ kv
        edges = tuple(hif_node_incidences(node, v, key="forward"))
    exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
    bases = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))
    ob = ob >> Box("(||)", ob.cod, exps >> bases)
    if tag:
        ob = ob @ exps >> Eval(exps >> bases) >> Box(tag, ob.cod, Ty(tag) >> Ty(tag))
    return ob

def _load_sequence(node, index, tag):
    ob = Id()
    for i, v in enumerate(iter_linked_list(node, index)):
        value = _load_node(node, v, None)
        if i == 0: ob = value
        else:
            bases, exps = ob.cod[0].inside[0].exponent, value.cod[0].inside[0].base
            ob = ob @ value >> Box("(;)", ob.cod, bases >> exps)
    if tag:
        bases = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
        exps = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))
        ob = bases @ ob >> Eval(bases >> exps) >> Box(tag, ob.cod, Ty() >> Ty(tag))
    return ob

def _load_document(node, index, _):
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    if not nxt: return Id()
    ((root_e, _, _, _), ) = nxt
    ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
    return _load_node(node, root, None)

def _load_stream(node, index, _):
    ob = Id()
    for nxt_node in iter_linked_list(node, index):
        doc = _load_node(node, nxt_node, None)
        ob = doc if ob == Id() else ob @ doc
    return ob
