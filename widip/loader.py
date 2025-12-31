from functools import reduce
from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all

from discopy.closed import Id, Ty, Box, Eval
from nx_hif.hif import HyperGraph

from . import hif
from .yaml import Scalar, Sequence, Mapping, Alias, Anchor


def get_exps_bases(cod):
    exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, cod))
    bases = Ty().tensor(*map(lambda x: x.inside[0].base, cod))
    return exps, bases


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
    data = hif.get_node_data(cursor)
    tag = (data.get("tag") or "")[1:]
    kind = data["kind"]
    anchor = data.get("anchor")

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
        case "alias":
            ob = load_alias(cursor, anchor)
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    if anchor and kind != 'alias':
        ob = ob >> Anchor(anchor, ob.cod, ob.cod)

    return ob

def load_alias(cursor, name):
    return Alias(name, Ty(), Ty() >> Ty(name))

def load_scalar(cursor, tag):
    data = hif.get_node_data(cursor)
    v = data["value"]
    return Scalar(tag, v)

def load_pair(pair):
    key, value = pair
    exps, _ = get_exps_bases(key.cod)
    _, bases = get_exps_bases(value.cod)
    kv_box = Sequence(key.cod @ value.cod, bases << exps, n=2)
    return key @ value >> kv_box

def load_mapping(cursor, tag):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    kvs = batched(diagrams, 2)

    kv_diagrams = list(map(load_pair, kvs))

    if not kv_diagrams:
        if tag:
            return Node(tag, Ty(), Ty(tag) >> Ty(tag))
        ob = Id()
    else:
        ob = reduce(lambda a, b: a @ b, kv_diagrams)

    exps, bases = get_exps_bases(ob.cod)
    par_box = Mapping(ob.cod, bases << exps)
    ob = ob >> par_box
    if tag:
        ob = (ob @ exps >> Eval(bases << exps))
        box = Node(tag, ob.cod, Ty(tag) >> Ty(tag))
        # box = Box("run", Ty(tag) @ ob.cod, Ty(tag)).curry(left=False)
        ob = ob >> box
    return ob

def load_sequence(cursor, tag):
    diagrams_list = list(map(_incidences_to_diagram, hif.iterate(cursor)))

    def reduce_fn(acc, value):
        combined = acc @ value
        bases = combined.cod[0].inside[0].exponent
        exps = value.cod[0].inside[0].base
        return combined >> Sequence(combined.cod, bases >> exps)

    if not diagrams_list:
        if tag:
            return Node(tag, Ty(), Ty(tag) >> Ty(tag))
        return Id()

    ob = reduce(reduce_fn, diagrams_list)

    if tag:
        bases, exps = get_exps_bases(ob.cod)
        ob = (bases @ ob >> Eval(bases >> exps))
        ob = ob >> Node(tag, ob.cod, Ty() >> Ty(tag))
    return ob

def load_document(cursor):
    root = hif.step(cursor, "next")
    if root:
        return _incidences_to_diagram(root)
    return Id()

def load_stream(cursor):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    return reduce(lambda a, b: a @ b, diagrams, Id())
