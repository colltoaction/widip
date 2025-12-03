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
    return
    """a diagram connecting equal objects within each type"""
    """glues two diagrams sequentially with closed generators"""
    if left.cod == right.dom:
        return left >> right
    l_dom, l_cod, r_dom, r_cod = left.dom, left.cod, right.dom, right.cod
    dw_l = {
        t
        for t in l_cod
        if t not in r_dom}
    dw_r = {
        t
        for t in r_dom
        if t not in l_cod}
    cw_l = {
        t
        for t in l_cod
        if t in r_dom}
    cw_r = {
        t
        for t in r_dom
        if t in l_cod}
    # TODO convention for repeated in both sides
    mid_names = tuple({t for t in l_cod + r_dom})
    dom_wires = l_dom_wires = tuple(
        i
        for i in range(len(l_dom) + len(dw_r))
    )
    l_cod_wires = tuple(
        (mid_names.index(t)
        + len(l_dom) + len(dw_r))
        for t in l_cod) + \
        tuple(
            (mid_names.index(t) + len(l_dom) + len(dw_r))
            for t in dw_r
        )
    r_dom_wires = tuple(
            (mid_names.index(t) + len(l_dom) + len(dw_r))
            for t in dw_l) + \
        tuple(
            (mid_names.index(t)
            + len(l_dom) + len(dw_r))
            for t in r_dom
        )
    cod_wires = r_cod_wires = tuple(
        i
        + len(l_dom) + len(dw_r)
        + len(mid_names)
        for i in range(len(dw_l) + len(r_cod))
    )
    glued = H(
        dom=l_dom @ Ty().tensor(*dw_r),
        cod=Ty().tensor(*dw_l) @ r_cod,
        boxes=(
            left @ Ty().tensor(*dw_r),
            Ty().tensor(*dw_l) @ right,
        ),
        wires=(
            dom_wires,
            (
                (l_dom_wires, l_cod_wires),
                (r_dom_wires, r_cod_wires),
            ),
            cod_wires,
        ),
    ).to_diagram()
    return glued

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