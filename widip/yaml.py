import functools
from contextlib import contextmanager
from contextvars import ContextVar
from itertools import batched
from discopy import closed
from nx_hif.hif import HyperGraph
from . import hif


diagram_var: ContextVar[closed.Diagram] = ContextVar("diagram")

class Node(closed.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)

class Scalar(closed.Box):
    def __init__(self, tag, value):
        dom = closed.Ty(value) if value else closed.Ty()
        cod = closed.Ty(tag) >> closed.Ty(tag) if tag else closed.Ty() >> closed.Ty(value)
        super().__init__("Scalar", dom, cod)

    @property
    def tag(self):
        if not self.cod or not self.cod[0].is_exp: return ""
        u = self.cod[0].inside[0]
        return u.base.name if u.base == u.exponent else ""

    @property
    def value(self):
        if self.dom: return self.dom[0].name
        if not self.cod or not self.cod[0].is_exp: return ""
        u = self.cod[0].inside[0]
        return u.base.name if not self.tag else ""

class Sequence(closed.Box):
    def __init__(self, dom, cod=None, n=2):
        if cod is None:
            if n == 2:
                mid = len(dom) // 2
                exps, _ = get_exps_bases(dom[:mid])
                _, bases = get_exps_bases(dom[mid:])
                cod = exps >> bases
            else:
                exps, bases = get_exps_bases(dom)
                cod = exps >> bases
        super().__init__("Sequence", dom, cod)

    @property
    def n(self):
        return len(self.dom)

class Mapping(closed.Box):
    def __init__(self, dom, cod=None):
        if cod is None:
            exps, bases = get_exps_bases(dom)
            cod = bases << exps
        super().__init__("Mapping", dom, cod)

class Anchor(closed.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)

class Alias(closed.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)

Yaml = closed.Category()


@contextmanager
def load_container(ob, tag, is_sequence):
    if not is_sequence:
        ob >>= Mapping(ob.cod)
    
    if tag:
        target = ob.cod
        exps, bases = get_exps_bases(target)
        if is_sequence:
            ob = exps @ ob
            ob >>= closed.Eval(target)
            ob >>= Node(tag, ob.cod, closed.Ty() >> closed.Ty(tag))
        else:
            ob @= exps
            ob >>= closed.Eval(target)
            ob >>= Node(tag, ob.cod, closed.Ty(tag) >> closed.Ty(tag))
            
    token = diagram_var.set(ob)
    try:
        yield
    finally:
        diagram_var.reset(token)

def get_exps_bases(cod):
    exps = closed.Ty().tensor(*[x.inside[0].exponent for x in cod])
    bases = closed.Ty().tensor(*[x.inside[0].base for x in cod])
    return exps, bases

def load_scalar(cursor, tag):
    data = hif.get_node_data(cursor)
    return Scalar(tag, data["value"])

def load_collection(cursor, tag, is_sequence, reduce_fn, transform_items=lambda x: x):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    items = list(transform_items(diagrams))
    if not items:
        if tag: return Node(tag, closed.Ty(), closed.Ty(tag) >> closed.Ty(tag))
        return closed.Id()
    
    ob = functools.reduce(reduce_fn, items)
    with load_container(ob, tag, is_sequence):
        return diagram_var.get()

def incidences_to_diagram(node: HyperGraph):
    cursor = (0, node)
    return _incidences_to_diagram(cursor)

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
            def reduce_seq(a, b):
                a @= b
                a >>= Sequence(a.cod)
                return a
            ob = load_collection(cursor, tag, True, reduce_seq)
        case "mapping":
            def transform_mapping_items(diagrams):
                for key, val in batched(diagrams, 2):
                    key @= val
                    key >>= Sequence(key.cod, n=2)
                    yield key
            ob = load_collection(cursor, tag, False, lambda a, b: a @ b, transform_mapping_items)
        case "alias":
            ob = Alias(anchor, closed.Ty(), closed.Ty() >> closed.Ty(anchor))
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    if anchor and kind != 'alias':
        ob >>= Anchor(anchor, ob.cod, ob.cod)
    return ob

def load_document(cursor):
    root = hif.step(cursor, "next")
    return _incidences_to_diagram(root) if root else closed.Id()

def load_stream(cursor):
    diagrams = map(_incidences_to_diagram, hif.iterate(cursor))
    return functools.reduce(lambda a, b: a @ b, diagrams, closed.Id())
