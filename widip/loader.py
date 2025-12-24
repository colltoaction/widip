from functools import reduce
from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

from discopy.closed import Id, Ty, Box, Eval

from .traverse import vertical_map, p_functor
from .hif_traverse import cursor_iter, cursor_step

P = Ty() << Ty("")


def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams

def incidences_to_diagram(node: HyperGraph):
    # TODO properly skip stream and document start
    cursor = (0, node)
    diagram = _incidences_to_diagram(cursor)
    return diagram

def _incidences_to_diagram(cursor):
    """
    Takes an nx_yaml rooted bipartite graph
    and returns an equivalent string diagram
    """
    node = p_functor(cursor)
    index = cursor[0]

    tag = (hif_node(node, index).get("tag") or "")[1:]
    kind = hif_node(node, index)["kind"]

    match kind:

        case "stream":
            ob = load_stream(cursor)
        case "document":
            ob = load_document(cursor)
        case "scalar":
            ob = load_scalar(cursor, tag)
        case "sequence":
            ob = load_sequence(cursor, tag)
        case "mapping":
            ob = load_mapping(cursor, tag)
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    return ob

def load_scalar(cursor, tag):
    node = p_functor(cursor)
    index = cursor[0]

    v = hif_node(node, index)["value"]
    if tag == "fix" and v:
        return Box("Ω", Ty(), Ty(v) << P) @ P \
            >> Eval(Ty(v) << P) \
            >> Box("e", Ty(v), Ty(v))
    if tag and v:
        return Box(tag, Ty(v), Ty(tag) >> Ty(tag))
    elif tag:
        dom = Ty(v) if v else Ty()
        return Box(tag, dom, Ty(tag) >> Ty(tag))
    elif v:
        return Box("⌜−⌝", Ty(v), Ty() >> Ty(v))
    else:
        return Box("⌜−⌝", Ty(), Ty() >> Ty(v))

def load_mapping(cursor, tag):
    diagrams = map(_incidences_to_diagram, cursor_iter(cursor))
    kvs = batched(diagrams, 2)

    def map_pair(pair):
        key, value = pair
        exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, key.cod))
        bases = Ty().tensor(*map(lambda x: x.inside[0].base, value.cod))
        kv_box = Box("(;)", key.cod @ value.cod, bases << exps)
        return key @ value >> kv_box

    kv_diagrams = list(map(map_pair, kvs))

    if not kv_diagrams:
        if tag:
            return Box(tag, Ty(), Ty(tag) >> Ty(tag))
        ob = Id()
    else:
        ob = reduce(lambda a, b: a @ b, kv_diagrams)

    exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
    bases = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))
    par_box = Box("(||)", ob.cod, bases << exps)
    ob = ob >> par_box
    if tag:
        ob = (ob @ exps >> Eval(bases << exps))
        box = Box(tag, ob.cod, Ty(tag) >> Ty(tag))
        # box = Box("run", Ty(tag) @ ob.cod, Ty(tag)).curry(left=False)
        ob = ob >> box
    return ob

def load_sequence(cursor, tag):
    diagrams_list = list(map(_incidences_to_diagram, cursor_iter(cursor)))

    def reduce_fn(acc, value):
        combined = acc @ value
        bases = combined.cod[0].inside[0].exponent
        exps = value.cod[0].inside[0].base
        return combined >> Box("(;)", combined.cod, bases >> exps)

    if not diagrams_list:
        if tag:
            return Box(tag, Ty(), Ty(tag) >> Ty(tag))
        return Id()

    ob = reduce(reduce_fn, diagrams_list)

    if tag:
        bases = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
        exps = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))
        ob = (bases @ ob >> Eval(bases >> exps))
        ob = ob >> Box(tag, ob.cod, Ty() >> Ty(tag))
    return ob

def load_document(cursor):
    root = cursor_step(cursor, "next")
    if root:
        return _incidences_to_diagram(root)
    return Id()

def load_stream(cursor):
    diagrams = map(_incidences_to_diagram, cursor_iter(cursor))
    return reduce(lambda a, b: a @ b, diagrams, Id())
