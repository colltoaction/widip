from discopy.frobenius import Hypergraph as H, Id, Ob, Ty, Box, Spider, Functor

def compose_entry(left, right):
    """connects two diagrams by removing the interfaces and connecting open wires"""
    if left == H.id(Ty("")) and right == H.id(Ty("")):
        return H.id(Ty(""))
    elif left == H.id(Ty("")):
        return right
    elif right == H.id(Ty("")):
        return left
    mid = adapter_hypergraph(left, right)
    return left >> mid >> right

def adapt_to_interface(diagram, box):
    """adapts a diagram open ports to fit in the box"""
    left = Id(box.dom)
    right = Id(box.cod)
    diagram = adapter_hypergraph(left, diagram) >> \
            diagram >> \
            adapter_hypergraph(diagram, right)
    g = diagram
    return g

def adapter_hypergraph(left, right):
    mid = Ty(*set(left.cod.inside + right.dom.inside))
    mid_to_left_ports = {
        t: tuple(i for i, lt in enumerate(left.cod) if lt == t)
        for t in mid}
    mid_to_right_ports = {
        t: tuple(i + len(left.cod) for i, lt in enumerate(right.dom) if lt == t)
        for t in mid}
    boxes = tuple(
        Id(Ty(*tuple(t.name for _ in range(len(mid_to_left_ports[t])))))
        if len(mid_to_left_ports[t]) == len(mid_to_right_ports[t]) else
        Spider(
            len(mid_to_left_ports[t]),
            len(mid_to_right_ports[t]),
            t)
        for t in mid)
    g = H(
        dom=left.cod, cod=right.dom,
        boxes=boxes,
        wires=(
            tuple(i for i in range(len(left.cod))),
            tuple(
                (mid_to_left_ports[t], mid_to_right_ports[t])
                for t in mid),
            tuple(i + len(left.cod) for i in range(len(right.dom))),
        ),
    )
    return g
