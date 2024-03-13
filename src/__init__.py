from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider

def diagram_functor(diagram):
    boxes = {
        Box("functor", box.dom, box.cod): box
        for box in diagram.boxes}
    return Functor(
        lambda ob: "functor" if ob.name == "" else ob,
        lambda ar: boxes.get(ar, ar))
