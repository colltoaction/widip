from discopy.closed import Id, Ty, Diagram, Functor, Box


def adapt_to_interface(diagram, box):
    return
    """adapts a diagram open ports to fit in the box"""
    left = Id(box.dom)
    right = Id(box.cod)
    return adapter_hypergraph(left, diagram) >> \
            diagram >> \
            adapter_hypergraph(diagram, right)

def adapter_hypergraph(left, right):
    return
    mid = Ty().tensor(*set(left.cod + right.dom))
    mid_to_left_ports = {
        t: tuple(i for i, lt in enumerate(left.cod) if lt == t)
        for t in mid}
    mid_to_right_ports = {
        t: tuple(i + len(left.cod) for i, lt in enumerate(right.dom) if lt == t)
        for t in mid}
    boxes = tuple(
        Id(Ty().tensor(*(t for _ in range(len(mid_to_left_ports[t])))))
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
    return g.to_diagram()

def glue_diagrams(left, right):
    # Use parallel composition as per memory instructions
    return left @ right

def replace_id_f(name):
    return Functor(
        lambda ob: replace_id_ty(ob, name),
        lambda ar: replace_id_box(ar, name),)

def replace_id_box(box, name):
    return Box(
        box.name,
        replace_id_ty(box.dom, name),
        replace_id_ty(box.cod, name))

def replace_id_ty(ty, name):
    return Ty().tensor(*(Ty("") if t == Ty(name) else t for t in ty))

def close_ty_f(name):
    return Functor(
        lambda ob: ob,#close_ty(ob, name),
        lambda ar: close_ty_box(ar, name),)

def close_ty_box(box, name):
    l = Ty().tensor(*(
        t for t in box.dom
        if t != Ty(name)))
    r = Ty().tensor(*(
        t for t in box.cod
        if t != Ty(name)))
    # box.draw()
    box.draw()
    closed = adapt_to_interface(box, Box("", l, r))
    closed.draw()
    return closed

def close_ty(ty, name):
    return Ty() if ty == Ty(name) else ty