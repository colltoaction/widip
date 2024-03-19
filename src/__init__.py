from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy.cat import Arrow

def replace_box(box: Box) -> Functor:
    return replace_arrow(box, box.name)

def replace_arrow(ar: Arrow, name) -> Functor:
    boxes = {
        Box(name, box.dom, box.cod): box
        for box in ar.boxes}
    return Functor(
        lambda ob: "" if ob.name == name else ob,
        lambda ar: boxes.get(ar, ar))
