from functools import reduce
from itertools import batched
from nx_yaml import nx_compose_all

from discopy.closed import Id, Ty, Box, Eval
from nx_hif.hif import HyperGraph

from . import hif
from .yaml import Scalar, Sequence, Mapping, Alias, Anchor
from .computer import Swap, Copy, Discard, Trace, Cast

def safe_swap(left, right):
    if not left:
        return Id(right)
    if not right:
        return Id(left)
    return Swap(left, right)

class Wire:
    def __init__(self, diagram, consumed, produced):
        self.diagram = diagram
        self.consumed = consumed  # list of (name, Ty)
        self.produced = produced  # list of (name, Ty)

    @property
    def dom(self):
        offset = len(self.consumed)
        if offset == 0:
            return self.diagram.dom
        return self.diagram.dom[: -offset]

    @property
    def cod(self):
        offset = len(self.produced)
        if offset == 0:
            return self.diagram.cod
        return self.diagram.cod[: -offset]

    def tensor(self, other):
        # self: I1 @ C1 -> O1 @ P1
        # other: I2 @ C2 -> O2 @ P2
        # Target: I1 @ I2 @ C1 @ C2 -> O1 @ O2 @ P1 @ P2

        c1_ty = sum_tys(t for n, t in self.consumed)
        c2_ty = sum_tys(t for n, t in other.consumed)
        p1_ty = sum_tys(t for n, t in self.produced)
        p2_ty = sum_tys(t for n, t in other.produced)

        # Input: I1 @ C1 @ I2 @ C2 -> I1 @ I2 @ C1 @ C2
        # Swap C1, I2.
        dom_perm = Id(self.dom) @ safe_swap(c1_ty, other.dom) @ Id(c2_ty)

        # Output: O1 @ P1 @ O2 @ P2 -> O1 @ O2 @ P1 @ P2
        # Swap P1, O2
        cod_perm = Id(self.cod) @ safe_swap(p1_ty, other.cod) @ Id(p2_ty)

        new_d = dom_perm >> (self.diagram @ other.diagram) >> cod_perm
        return Wire(new_d, self.consumed + other.consumed, self.produced + other.produced)

    def then(self, other):
        # self: I1 @ C1 -> O1 @ P1
        # other: I2 @ C2 -> O2 @ P2
        # O1 == I2
        # Target: I1 @ C1 @ C2 -> O2 @ P1 @ P2

        c2_ty = sum_tys(t for n, t in other.consumed)
        step1 = self.diagram @ Id(c2_ty) # Out: O1 @ P1 @ C2

        p1_ty = sum_tys(t for n, t in self.produced)
        swap_layer = Id(self.cod) @ safe_swap(p1_ty, c2_ty) # Out: O1 @ C2 @ P1

        step2 = other.diagram @ Id(p1_ty)

        new_d = step1 >> swap_layer >> step2
        return Wire(new_d, self.consumed + other.consumed, other.produced + self.produced)

    def __matmul__(self, other):
        return self.tensor(other)

    def __rshift__(self, other):
        return self.then(other)

def sum_tys(tys):
    return reduce(lambda a, b: a @ b, tys, Ty())

def wrap(box):
    return Wire(box, [], [])

def repl_read(stream):
    incidences = nx_compose_all(stream)
    diagrams = incidences_to_diagram(incidences)
    return diagrams

def incidences_to_diagram(node: HyperGraph):
    cursor = (0, node)
    wire = _incidences_to_diagram(cursor)
    final_diagram = trace_wires(wire)
    return final_diagram

def _incidences_to_diagram(cursor):
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
        # ob is Wire
        val_ty = ob.cod
        anchor_ty = Ty(anchor)

        copy_box = Copy(val_ty, 2)
        cast_box = Cast(val_ty, anchor_ty)

        layer = copy_box >> (Id(val_ty) @ cast_box)

        p_ty = sum_tys(t for n, t in ob.produced)

        swap_layer = Id(val_ty) @ safe_swap(anchor_ty, p_ty)

        final_d = ob.diagram >> (layer @ Id(p_ty)) >> swap_layer
        ob = Wire(final_d, ob.consumed, ob.produced + [(anchor, anchor_ty)])

    return ob

def load_alias(cursor, name):
    t = Ty(name)
    d = Id(t).curry(n=0, left=False)
    return Wire(d, [(name, t)], [])

def load_scalar(cursor, tag):
    data = hif.get_node_data(cursor)
    v = data["value"]
    return wrap(Scalar(tag, v))

def load_pair(pair):
    key, value = pair
    exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, key.cod))
    bases = Ty().tensor(*map(lambda x: x.inside[0].base, value.cod))
    kv_box = Sequence(key.cod @ value.cod, bases << exps, n=2)

    return key @ value >> wrap(kv_box)

def load_mapping(cursor, tag):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    kvs = batched(diagrams, 2)

    kv_diagrams = list(map(load_pair, kvs))

    if not kv_diagrams:
        if tag:
            return wrap(Box(tag, Ty(), Ty(tag) >> Ty(tag)))
        return wrap(Id())
    else:
        ob = reduce(lambda a, b: a @ b, kv_diagrams)

    exps = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
    bases = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))

    par_box = Mapping(ob.cod, bases << exps)
    ob = ob >> wrap(par_box)

    if tag:
        w_exps = wrap(Id(exps))
        eval_box = Eval(bases << exps)
        w_eval = wrap(eval_box)

        ob = (ob @ w_exps) >> w_eval

        box = Box(tag, ob.cod, Ty(tag) >> Ty(tag))
        ob = ob >> wrap(box)
    return ob

def load_sequence(cursor, tag):
    diagrams_list = list(map(_incidences_to_diagram, hif.iterate(cursor)))

    def reduce_fn(acc, value):
        combined = acc @ value
        bases = combined.cod[0].inside[0].exponent
        exps = value.cod[0].inside[0].base
        seq_box = Sequence(combined.cod, bases >> exps)
        return combined >> wrap(seq_box)

    if not diagrams_list:
        if tag:
            return wrap(Box(tag, Ty(), Ty(tag) >> Ty(tag)))
        return wrap(Id())

    ob = reduce(reduce_fn, diagrams_list)

    if tag:
        bases = Ty().tensor(*map(lambda x: x.inside[0].exponent, ob.cod))
        exps = Ty().tensor(*map(lambda x: x.inside[0].base, ob.cod))

        w_bases = wrap(Id(bases))
        w_eval = wrap(Eval(bases >> exps))

        ob = (w_bases @ ob) >> w_eval
        ob = ob >> wrap(Box(tag, ob.cod, Ty() >> Ty(tag)))
    return ob

def load_document(cursor):
    root = hif.step(cursor, "next")
    if root:
        return _incidences_to_diagram(root)
    return wrap(Id())

def load_stream(cursor):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    return reduce(lambda a, b: a @ b, diagrams, wrap(Id()))

def sort_list(d, metadata, is_codomain):
    n = len(metadata)
    meta = list(metadata)

    if is_codomain:
        types = list(d.cod)
        offset = len(types) - n
    else:
        types = list(d.dom)
        offset = len(types) - n

    for i in range(n):
        for j in range(0, n - i - 1):
            if meta[j][0] > meta[j+1][0]:
                idx = offset + j
                t1 = meta[j][1]
                t2 = meta[j+1][1]

                if is_codomain:
                    pre = sum_tys(types[:idx])
                    post = sum_tys(types[idx+2:])
                    layer = Id(pre) @ Swap(t1, t2) @ Id(post)
                    d = d >> layer
                    types[idx], types[idx+1] = types[idx+1], types[idx]
                else:
                    pre = sum_tys(types[:idx])
                    post = sum_tys(types[idx+2:])
                    layer = Id(pre) @ Swap(t1, t2) @ Id(post)
                    d = layer >> d
                    types[idx], types[idx+1] = types[idx+1], types[idx]

                meta[j], meta[j+1] = meta[j+1], meta[j]

    return d, meta

def trace_wires(wire):
    d = wire.diagram
    d, sorted_cons = sort_list(d, wire.consumed, is_codomain=False)
    d, sorted_prod = sort_list(d, wire.produced, is_codomain=True)

    cons_map = {}
    for n, t in sorted_cons:
        cons_map[n] = cons_map.get(n, 0) + 1

    prod_map = {}
    for n, t in sorted_prod:
        prod_map[n] = prod_map.get(n, 0) + 1

    common = sorted(list(set(cons_map.keys()) & set(prod_map.keys())), reverse=True)

    for name in common:
        if prod_map[name] > 1:
            raise Exception(f"Multiple producers for {name}")

        n_cons = cons_map[name]
        ty = sorted_prod[-1][1]

        pre_prod = d.cod[: -1]
        d = d >> (Id(pre_prod) @ Copy(ty, n_cons))
        sorted_prod.pop()

        for _ in range(n_cons):
             d = Trace(d)
             sorted_cons.pop()

    return d
