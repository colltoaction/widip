from functools import reduce
from itertools import batched
from contextlib import contextmanager
import contextvars
from dataclasses import dataclass, field

from nx_yaml import nx_compose_all, nx_serialize_all

from discopy import closed
from discopy.closed import Id, Ty, Box, Eval
from nx_hif.hif import HyperGraph

from . import hif
from .yaml import Scalar, Sequence, Mapping, Alias, Anchor
from .computer import Copy, Trace, Swap, Cast

@dataclass
class Scope:
    anchor: str | None = None
    aliases: list = field(default_factory=list)

alias_var = contextvars.ContextVar("aliases", default=None)

@contextmanager
def alias_scope(anchor=None):
    parent = alias_var.get()
    current = Scope(anchor=anchor)
    token = alias_var.set(current)
    try:
        yield current, parent
    finally:
        alias_var.reset(token)

def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams

def incidences_to_diagram(node: HyperGraph):
    # Top level scope
    with alias_scope(anchor=None) as (scope, parent):
        cursor = (0, node)
        diagram = _incidences_to_diagram(cursor)
        return diagram

def make_permutation(dom, perm):
    n = len(dom)
    if n != len(perm):
        raise ValueError("Permutation length mismatch")

    p_inv = [0] * n
    for i, p in enumerate(perm):
        p_inv[p] = i

    current = list(range(n))
    diagram = Id(dom)

    for i in range(n):
        desired = p_inv[i]
        current_pos = current.index(desired)

        for j in range(current_pos, i, -1):
            layer_cod = diagram.cod
            left = layer_cod[j-1]
            right = layer_cod[j]
            swap_box = Swap(left, right)
            layer = Id(layer_cod[:j-1]) @ swap_box @ Id(layer_cod[j+1:])
            diagram = diagram >> layer
            current[j-1], current[j] = current[j], current[j-1]

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

    if anchor and kind != 'alias':
        with alias_scope(anchor=anchor) as (scope, parent):
            ob = load_dispatch(cursor, kind, tag, anchor)
            ob, remaining = resolve_anchor(ob, scope.aliases, anchor)
            if parent is not None:
                parent.aliases.extend(remaining)
            return ob
    else:
        return load_dispatch(cursor, kind, tag, anchor)

def load_dispatch(cursor, kind, tag, anchor):
    match kind:
        case "stream":
            return load_stream(cursor)
        case "document":
            return load_document(cursor)
        case "scalar":
            return load_scalar(cursor, tag)
        case "sequence":
            return load_sequence(cursor, tag)
        case "mapping":
            return load_mapping(cursor, tag)
        case "alias":
            return load_alias(cursor, anchor)
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

def resolve_anchor(ob, ctx, anchor_name):
    indices = [i for i, name in enumerate(ctx) if name == anchor_name]

    ob = ob >> Anchor(anchor_name, ob.cod, ob.cod)

    if not indices:
        return ob, ctx

    n_aliases = len(indices)
    cod = ob.cod

    ob = ob >> Copy(cod, n_aliases + 1)

    dom_layers = ob.dom
    n_inputs = len(dom_layers)
    non_alias_indices = [i for i in range(n_inputs) if i not in indices]
    new_order_indices = non_alias_indices + indices

    new_dom_list = [dom_layers[i] for i in new_order_indices]
    new_dom = sum(new_dom_list, Ty())

    perm_box = make_permutation(new_dom, new_order_indices)

    combined = perm_box >> ob

    alias_type = dom_layers[indices[0]]
    if cod != alias_type:
        cast_box = Cast(cod, alias_type)
        casts = Id(cod)
        for _ in range(n_aliases):
            casts = casts @ cast_box
        combined = combined >> casts

    ob = Trace(combined)

    new_ctx = [ctx[i] for i in non_alias_indices]

    return ob, new_ctx

def load_alias(cursor, name):
    t = Ty() >> Ty(name)
    current = alias_var.get()
    if current is not None:
        current.aliases.append(name)
    return Id(t)

def load_scalar(cursor, tag):
    data = hif.get_node_data(cursor)
    v = data["value"]
    s = Scalar(tag, v)
    current = alias_var.get()
    if current is not None:
        current.aliases.extend([None] * len(s.dom))
    return s

def load_pair(pair):
    key_d, val_d = pair
    exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, key_d.cod))
    bases = Ty().tensor(*map(lambda x: x.inside[0].base, val_d.cod))
    kv_box = Sequence(key_d.cod @ val_d.cod, bases << exps, n=2)
    diag = key_d @ val_d >> kv_box
    return diag

def load_mapping(cursor, tag):
    results = list(map(_incidences_to_diagram, hif.iterate(cursor)))
    kvs = batched(results, 2)
    kv_results = list(map(load_pair, kvs))

    if not kv_results:
        if tag:
            return Box(tag, Ty(), Ty(tag) >> Ty(tag))
        ob = Id()
        return ob

    ob_d = reduce(lambda a, b: a @ b, kv_results)

    exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob_d.cod))
    bases = Ty().tensor(*map(lambda x: x.inside[0].base, ob_d.cod))
    par_box = Mapping(ob_d.cod, bases << exps)
    ob_d = ob_d >> par_box

    if tag:
        ob_d = (ob_d @ exps >> Eval(bases << exps))

        # Update alias scope for exps inputs
        current = alias_var.get()
        if current is not None:
            current.aliases.extend([None] * len(exps))

        box = Box(tag, ob_d.cod, Ty(tag) >> Ty(tag))
        ob_d = ob_d >> box

    return ob_d

def load_sequence(cursor, tag):
    results = list(map(_incidences_to_diagram, hif.iterate(cursor)))

    def reduce_fn(acc, value):
        combined = acc @ value
        bases = combined.cod[0].inside[0].exponent
        exps = value.cod[0].inside[0].base
        return combined >> Sequence(combined.cod, bases >> exps)

    if not results:
        if tag:
            return Box(tag, Ty(), Ty(tag) >> Ty(tag))
        return Id()

    ob_d = reduce(reduce_fn, results)

    if tag:
        bases = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob_d.cod))
        exps = Ty().tensor(*map(lambda x: x.inside[0].base, ob_d.cod))
        ob_d = (bases @ ob_d >> Eval(bases >> exps))

        # Update alias scope for exps inputs
        current = alias_var.get()
        if current is not None:
            current.aliases.extend([None] * len(exps))

        ob_d = ob_d >> Box(tag, ob_d.cod, Ty() >> Ty(tag))

    return ob_d

def load_document(cursor):
    root = hif.step(cursor, "next")
    if root:
        return _incidences_to_diagram(root)
    return Id()

def load_stream(cursor):
    results = map(_incidences_to_diagram, hif.iterate(cursor))
    return reduce(lambda a, b: a @ b, results, Id())
