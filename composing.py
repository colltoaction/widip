from discopy.frobenius import Hypergraph as H, Id, Ty, Spider, Swap, Diagram


def adapt_to_interface(diagram, box):
    """adapts a diagram open ports to fit in the box"""
    left = Id(box.dom)
    right = Id(box.cod)
    return glue_diagrams(left, diagram) >> \
            diagram >> \
            glue_diagrams(diagram, right)

def glue_diagrams(left, right):
    """a diagram connecting equal objects within each type"""
    """glues two diagrams sequentially with frobenius generators"""
    l_dom, l_cod, r_dom, r_cod = left.dom, left.cod, right.dom, right.cod
    dw_l = {
        t.name
        for t in l_cod
        if t not in r_dom}
    dw_r = {
        t.name
        for t in r_dom
        if t not in l_cod}
    cw_l = {
        t.name
        for t in l_cod
        if t in r_dom}
    cw_r = {
        t.name
        for t in r_dom
        if t in l_cod}
    # TODO convention for repeated in both sides
    mid_names = tuple({t.name for t in l_cod + r_dom})
    dom_wires = l_dom_wires = tuple(
        i
        for i in range(len(l_dom) + len(dw_r))
    )
    l_cod_wires = tuple(
        (mid_names.index(t.name)
        + len(l_dom) + len(dw_r))
        for t in l_cod) + \
        tuple(
            (mid_names.index(n) + len(l_dom) + len(dw_r))
            for n in dw_r
        )
    r_dom_wires = tuple(
            (mid_names.index(n) + len(l_dom) + len(dw_r))
            for n in dw_l) + \
        tuple(
            (mid_names.index(t.name)
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
        dom=l_dom @ Ty(*dw_r),
        cod=Ty(*dw_l) @ r_cod,
        boxes=(
            left @ Ty(*dw_r),
            Ty(*dw_l) @ right,
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

def glue_all_diagrams(file_diagrams) -> Diagram:
    i = 0
    diagram = None
    for d in file_diagrams:
        if i == 0:
            diagram = d
        else:
            diagram = glue_diagrams(diagram, d)
        i += 1
    if i == 0:
        return Id()
    return diagram
