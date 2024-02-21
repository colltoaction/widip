import pathlib
import yaml
from discopy.frobenius import Box, Ty, Spider, Diagram, Id, Functor, Category, Hypergraph as H
from discopy import python

from files import compose_graph_file
from loader import compose_entry

b, t, f = Ty("bool"), Ty("true"), Ty("false")
# not_bool = Box("not", b, b)
not_true = Box("not", t, f)
not_false = Box("not", f, t)
t_box = Box("bool", t, t)
f_box = Box("bool", f, f)


def test_bool():
    path = "src/yaml/data/bool.yaml"
    bool_functor = graph_to_functor("bool", path)
    assert bool_functor(Box("bool", t, t)) == Id(t)
    assert bool_functor(Box("bool", f, f)) == Id(f)
    assert bool_functor(Box("bool", Ty(), Ty())) == Id()
    assert bool_functor(Box("bool", Ty(), f)) == Spider(0, 1, f)
    assert bool_functor(Box("bool", Ty(), t)) == Spider(0, 1, t)
    assert bool_functor(Box("bool", f, Ty())) == Spider(1, 0, f)
    assert bool_functor(Box("bool", t, Ty())) == Spider(1, 0, t)

# def test_bool_not():
#     bool_functor = graph_to_functor("bool", "src/yaml/data/bool.yaml")
#     path = "src/yaml/data/bool/not.yaml"
#     bool_not_functor = graph_to_functor("not", path)
#     # bool_not_functor = bool_not_functor >> bool_functor
#     assert bool_functor(bool_not_functor(t_box >> not_true >> not_false)).draw() == remove_box(t_box)
#     assert bool_not_functor(not_false >> not_true) == remove_box(f_box)

# def test_bool_and():
#     bool_diagram = compose_graph_file(pathlib.Path("src/yaml/data/bool.yaml"))
#     bool_and_diagram = compose_graph_file(pathlib.Path("src/yaml/data/bool/and.yaml"))
#     d = bool_diagram#compose_entry(bool_diagram.to_hypergraph(), bool_and_diagram.to_hypergraph())
#     # TyToBool = Functor(ob=lambda x: b if x == Ty("") else x, ar=lambda x: x)
#     # d.draw()
#     # d = TyToBool(d)
#     # d.draw()
#     and_boxes = {
#         Box("and", bn.dom, bn.cod): remove_box(bn)
#         for bn in set(bool_and_diagram.boxes)}
#     print(and_boxes)
#     bool_and_functor = Functor(
#         ob=lambda x: x,
#         ar=and_boxes)
#     # print(bool_and_functor)
#     assert bool_and_functor(Box("and", t @ f, f))
#     # assert bool_and_functor(Box("and", t @ f, b)) == Id(f)
#     # assert bool_and_functor(Box("and", f @ t, b)) == Id(f)
#     # assert bool_and_functor(Box("and", f @ f, b)) == Id(f)
#     # assert bool_and_functor(Box("and", t @ t, b)) == Id(t)


def graph_to_functor(tag, path):
    bool_diagram = compose_graph_file(pathlib.Path(path))
    boxes = {
        Box(tag, bn.dom, bn.cod): remove_box(bn)
        for bn in set(bool_diagram.boxes)}
    bool_functor = Functor(
        ob=lambda x: x,
        ar=lambda x: boxes.get(x, x))
    return bool_functor

def remove_box(bn):
    # TODO remove bones
    if bn.dom == bn.cod:
        return Id(bn.dom)
    l = H.spiders(1, 0, bn.dom).to_diagram() if bn.dom else Id()
    r = H.spiders(0, 1, bn.cod).to_diagram() if bn.cod else Id()
    return l >> r