from discopy.frobenius import Hypergraph as H, Id, Ty, Box, Functor, Spider


def glue_diagrams(left, right):
    """glues two diagrams sequentially with frobenius generators"""
    if left == Id(Ty("")) and right == Id(Ty("")):
        return Id(Ty(""))
    elif left == Id(Ty("")):
        return right
    elif right == Id(Ty("")):
        return left
    mid = frobenius_cospan(left.cod, right.dom)
    return left >> mid >> right

def eval_by_rewriting(d, p):
    """closes the left diagram's open wires present in the right parameters"""
    left = Id().tensor(*(
        Spider(0, 1, x) if x in p.dom else Id(x)
        for x in d.dom))
    right = Id().tensor(*(
        Spider(1, 0, x) if x not in p.cod else Id(x)
        for x in d.cod))
    return left >> d >> right

def box_expansion_functor():
    return Functor(lambda x: x, box_expansion)

def box_expansion(box):
    i = Id().tensor(*(Box(n.name, n, Ty(box.name)) for n in box.dom))
    o = Id().tensor(*(Box(n.name, Ty(box.name), n) for n in box.cod))
    return glue_diagrams(i, o)

def frobenius_cospan(dom: Ty, cod: Ty):
    """a diagram connecting equal objects within each type"""
    mid = Ty(*set(dom.inside + cod.inside))
    mid_to_left_ports = {
        t: tuple(i for i, lt in enumerate(dom) if lt == t)
        for t in mid}
    mid_to_right_ports = {
        t: tuple(i + len(dom) for i, lt in enumerate(cod) if lt == t)
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
        dom=dom, cod=cod,
        boxes=boxes,
        wires=(
            tuple(i for i in range(len(dom))),
            tuple(
                (mid_to_left_ports[t], mid_to_right_ports[t])
                for t in mid),
            tuple(i + len(dom) for i in range(len(cod))),
        ),
    )
    return g.to_diagram()
