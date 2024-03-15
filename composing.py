from discopy.frobenius import Hypergraph as H, Id, Ty, Box, Functor, Spider


def glue_diagrams(left, right):
    """glues two diagrams sequentially with frobenius generators"""
    # if left == Id(Ty("")) and right == Id(Ty("")):
    #     return Id(Ty(""))
    # elif left == Id(Ty("")):
    #     return right
    # elif right == Id(Ty("")):
    #     return left
    mid = frobenius_cospan(left.cod, right.dom)
    glued = left >> mid >> right
    return glued

def expand_name_functor(name):
    ob = lambda x: replace_id_ty(x, name)
    ar = lambda ar: box_expansion(ar) if ar.name == name else replace_id_box(ar, name)
    return Functor(ob, ar)

def box_expansion(box):
    i_ty = replace_id_ty(box.dom, box.name)
    o_ty = replace_id_ty(box.cod, box.name)
    i = Id().tensor(*(Box(n.name, n, Ty(box.name)) for n in i_ty))
    o = Id().tensor(*(Box(n.name, Ty(box.name), n) for n in o_ty))
    io = glue_diagrams(i, o)
    return io

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

def replace_id_box(box, name):
    if box.dom.name == name == box.cod.name:
        return Id(name)
    return Box(
        box.name,
        replace_id_ty(box.dom, name),
        replace_id_ty(box.cod, name))

def replace_id_ty(ty, name):
    return Ty(*(name if x.name == "" else x.name for x in ty.inside))
