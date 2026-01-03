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
Copy = lambda x, n=2: symmetric.Box(f"Copy({x}, {n})", x, x ** n)
Merge = lambda x, n=2: symmetric.Box(f"Merge({x}, {n})", x ** n, x)
Discard = lambda x: symmetric.Box(f"Discard({x})", x, symmetric.Ty())
Swap = symmetric.Swap

diagram_var: ContextVar[symmetric.Diagram] = ContextVar("diagram")
inside_tag_var: ContextVar[bool] = ContextVar("inside_tag", default=False)

@contextmanager
def load_container(cursor):
    token = diagram_var.set(cursor)
    try:
        yield hif.iterate(cursor)
    finally:
        diagram_var.reset(token)

def to_symmetric(diag, depth=0):
    """Convert any diagram to symmetric"""
    if depth > 10:
        # Prevent infinite recursion - try to preserve type info
        if hasattr(diag, 'dom') and hasattr(diag, 'cod'):
            return symmetric.Id(diag.dom)
        return symmetric.Id(symmetric.Ty())
        
    if isinstance(diag, symmetric.Diagram):
        return diag
    if hasattr(diag, 'dom') and hasattr(diag, 'cod'):
        return symmetric.Id(diag.dom) >> diag
    return diag

def bridge(left, right):
    # Ensure both are symmetric diagrams
    left = to_symmetric(left)
    right = to_symmetric(right)
        
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

def load_scalar(cursor, tag):
    data = hif.get_node_data(cursor)
    return Scalar(tag, data["value"])

def load_sequence(cursor, tag):
    diagrams = []
    token = None
    if tag:
        token = inside_tag_var.set(True)
    
    try:
        with load_container(cursor) as items:
            for item in items:
                diagrams.append(_incidences_to_diagram(item))

        if not diagrams:
            ob = Scalar(tag, "")
        else:
            if inside_tag_var.get():
                # Parallel arguments/elements - use symmetric tensor
                ob = diagrams[0]
                for d in diagrams[1:]:
                    # Ensure both are symmetric diagrams
                    left = to_symmetric(ob)
                    right = to_symmetric(d)
                    # Use symmetric tensor composition
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

def load_mapping(cursor, tag):
    items = []
    token = None
    if tag:
        token = inside_tag_var.set(True)
    
    try:
        with load_container(cursor) as nodes:
            diagrams_list = list(map(_incidences_to_diagram, nodes))

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

        # Implicitly copy input and merge results from all branches - use symmetric tensor
        tensor = items[0]
        for item in items[1:]:
            left = to_symmetric(tensor)
            right = to_symmetric(item)
            tensor = left.tensor(right)
        
        connector = Copy(common_dom, len(items))
        merger = Merge(items[0].cod if items else Node, len(items))
        ob = to_symmetric(connector) >> tensor >> to_symmetric(merger)
    
    if tag:
        # Ensure the internal diagram is compatible with the bubble's dom=Node
        ob = bridge(symmetric.Id(Node), ob)
        # Return bubble for tagged mappings
        return Mapping(ob, tag=tag)
    # Return diagram directly for untagged mappings
    return ob

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
            ob = load_sequence(cursor, tag)
        case "mapping":
            ob = load_mapping(cursor, tag)
        case "alias":
            ob = Alias(anchor)
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    if anchor and kind != 'alias':
        # For anchors, just return the diagram - don't wrap in bubble
        # The anchor name is stored but we return the inner diagram
        return ob
    return ob

def load_document(cursor):
    root = hif.step(cursor, "next")
    return _incidences_to_diagram(root) if root else symmetric.Id(symmetric.Ty())

def load_stream(cursor):
    diagrams = list(map(_incidences_to_diagram, hif.iterate(cursor)))
    if not diagrams:
        return symmetric.Id(symmetric.Ty())
    # A stream is an I -> I bubble, reduced with >>
    result = diagrams[0]
    for d in diagrams[1:]:
        result = bridge(to_symmetric(result), to_symmetric(d))
    
    return to_symmetric(result)
