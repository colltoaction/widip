from functools import reduce
from contextlib import contextmanager
from contextvars import ContextVar
from itertools import batched

from discopy import symmetric, monoidal
from nx_hif.hif import HyperGraph

import sys
from . import hif
from .yaml import Node, Scalar, Sequence, Mapping, Anchor, Alias

# Symmetric category structural boxes (markov.Copy/Merge/Discard are incompatible)
class Copy(symmetric.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Copy({x}, {n})", x, x ** n)
        self.n = n

class Merge(symmetric.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Merge({x}, {n})", x ** n, x)
        self.n = n

class Discard(symmetric.Box):
    def __init__(self, x):
        super().__init__(f"Discard({x})", x, symmetric.Ty())

Swap = symmetric.Swap

diagram_var: ContextVar[symmetric.Diagram] = ContextVar("diagram")
inside_tag_var: ContextVar[bool] = ContextVar("inside_tag", default=False)

@contextmanager
def load_container(index, node):
    token = diagram_var.set((index, node))
    try:
        yield hif.iterate(index, node)
    finally:
        diagram_var.reset(token)

def to_traced(diag):
    if isinstance(diag, symmetric.Diagram):
        return diag
    return symmetric.Id(diag.dom) >> diag

def bridge(left, right):
    # Ensure both are traced diagrams
    left = to_traced(left)
    right = to_traced(right)
        
    if left.cod == right.dom:
        return left >> right
    
    # Pad with Discard/Scalar to match domains
    if len(left.cod) > len(right.dom):
        # Discard excess from left
        diff = len(left.cod) - len(right.dom)
        discards = symmetric.Id().tensor(*[Discard(left.cod[i:i+1]) for i in range(diff)])
        return left >> (discards @ right)
    elif len(left.cod) < len(right.dom):
        # Source missing from right
        diff = len(right.dom) - len(left.cod)
        sources = symmetric.Id().tensor(*[Scalar("", "", dom=symmetric.Ty(), cod=right.dom[i:i+1]) for i in range(diff)])
        return left >> (sources @ right)
    
    return left >> right

def load_scalar(index, node, tag):
    data = hif.get_node_data(index, node)
    return Scalar(tag, data["value"])

def load_sequence(index, node, tag):
    diagrams = []
    token = None
    if tag:
        token = inside_tag_var.set(True)
    
    try:
        with load_container(index, node) as items:
            for idx, nd in items:
                diagrams.append(_incidences_to_diagram(idx, nd))

        if not diagrams:
            ob = Scalar(tag, "")
        else:
            if inside_tag_var.get():
                # Parallel arguments/elements - use traced tensor
                ob = diagrams[0]
                for d in diagrams[1:]:
                    # Ensure both are traced diagrams
                    left = to_traced(ob)
                    right = to_traced(d)
                    # Use traced tensor composition
                    ob = left.tensor(right)
            else:
                # Sequential steps
                ob = diagrams[0]
                for next_diag in diagrams[1:]:
                    ob = bridge(ob, next_diag)
    finally:
        if token:
            inside_tag_var.reset(token)

    if tag:
         # Ensure the internal diagram is compatible with the bubble's dom=Node
         ob = bridge(symmetric.Id(Node), ob)
         # Return bubble for tagged sequences
         return Sequence(ob, tag=tag)
    # Return diagram directly for untagged sequences
    return ob

def load_mapping(index, node, tag):
    items = []
    token = None
    if tag:
        token = inside_tag_var.set(True)
    
    try:
        with load_container(index, node) as nodes:
            diagrams_list = list(_incidences_to_diagram(idx, nd) for idx, nd in nodes)

            for key, val in batched(diagrams_list, 2):
                if isinstance(key, Scalar) and not key.tag and not key.value:
                     continue
                
                if isinstance(val, Scalar) and not val.tag and not val.value:
                     val = symmetric.Id(key.cod)

                # Mapping entries are Key >> Value
                items.append(bridge(key, val))
    finally:
        if token:
            inside_tag_var.reset(token)

    if not items:
        ob = Scalar(tag, "")
    else:
        # Uniform the domains
        common_dom = symmetric.Ty()
        if any(len(item.dom) > 0 for item in items):
             common_dom = Node
        
        items = [bridge(symmetric.Id(common_dom), item) for item in items]

        # Implicitly copy input and merge results from all branches - use traced tensor
        tensor = items[0]
        for item in items[1:]:
            left = to_traced(tensor)
            right = to_traced(item)
            tensor = left.tensor(right)
        
        connector = Copy(common_dom, len(items))
        merger = Merge(items[0].cod if items else Node, len(items))
        ob = to_traced(connector) >> tensor >> to_traced(merger)
    
    if tag:
        # Ensure the internal diagram is compatible with the bubble's dom=Node
        ob = bridge(symmetric.Id(Node), ob)
        # Return bubble for tagged mappings
        return Mapping(ob, tag=tag)
    # Return diagram directly for untagged mappings
    return ob

def incidences_to_diagram(node):
    return _incidences_to_diagram(0, node)

def _incidences_to_diagram(index, node):
    data = hif.get_node_data(index, node)
    tag = (data.get("tag") or "")[1:]
    kind = data["kind"]
    anchor = data.get("anchor")

    match kind:
        case "stream":
            ob = load_stream(index, node)
        case "document":
            ob = load_document(index, node)
        case "scalar":
            ob = load_scalar(index, node, tag)
        case "sequence":
            ob = load_sequence(index, node, tag)
        case "mapping":
            ob = load_mapping(index, node, tag)
        case "alias":
            ob = Alias(anchor)
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    if anchor and kind != 'alias':
        return Anchor(anchor, ob)
    return ob

def load_document(index, node):
    root = hif.step(index, node, "next")
    return _incidences_to_diagram(root[0], root[1]) if root else symmetric.Id(symmetric.Ty())

def load_stream(index, node):
    diagrams = list(_incidences_to_diagram(idx, nd) for idx, nd in hif.iterate(index, node))
    if not diagrams:
        return symmetric.Id(symmetric.Ty())
    # A stream is an I -> I bubble, reduced with >>
    result = diagrams[0]
    for d in diagrams[1:]:
        result = bridge(to_traced(result), to_traced(d))
    
    return to_traced(result)
