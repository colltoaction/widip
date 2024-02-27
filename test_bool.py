import pathlib
import yaml
from discopy.frobenius import Box, Ty, Spider, Diagram, Id, Functor, Category, Hypergraph as H
from discopy import python

from files import compose_graph_file, file_functor

b, t, f = Ty("bool"), Ty("true"), Ty("false")
# not_bool = Box("not", b, b)
not_true = Box("not", t, f)
not_false = Box("not", f, t)
t_box = Box("bool", t, t)
f_box = Box("bool", f, f)


# def test_bool():
#     path = "src/yaml/data/bool.yaml"
#     bool_functor = graph_to_functor("bool", path)
#     with Diagram.hypergraph_equality:
#         assert bool_functor(Box("bool", t, t)) == Spider(0, 0, f) @ Id(t)
#         assert bool_functor(Box("bool", f, f)) == Id(f) @ Spider(0, 0, t)
#         assert bool_functor(Box("bool", Ty(), Ty())) == Spider(0, 0, f) @ Spider(0, 0, t)
#         assert bool_functor(Box("bool", Ty(), f)) == Spider(0, 1, f) @ Spider(0, 0, t)
#         assert bool_functor(Box("bool", Ty(), t)) == Spider(0, 0, f) @ Spider(0, 1, t)
#         assert bool_functor(Box("bool", f, Ty())) == Spider(1, 0, f) @ Spider(0, 0, t)
#         assert bool_functor(Box("bool", t, Ty())) == Spider(0, 0, f) @ Spider(1, 0, t)

# def test_bool_not():
#     path = "src/yaml/data/bool/not.yaml"
#     # bool_functor = graph_to_functor("bool", path)
#     not_functor = graph_to_functor("not", path)
#     functor = not_functor
#     with Diagram.hypergraph_equality:
#         assert functor(Box("not", t, f)).draw() == Spider(0, 0, f) @ Id(t)

def test_bool_full():
    test_diagram = compose_graph_file("test/yaml/data/bool.yaml")
    functor = file_functor() >> file_functor()
    with Diagram.hypergraph_equality:
        assert functor(test_diagram).draw() == Spider(0, 0, f) @ Id(t)

# def test_bool_and():
#     bool_diagram = compose_graph_file("src/yaml/data/bool.yaml"))
#     not_diagram = compose_graph_file("src/yaml/data/bool/not.yaml"))
#     and_diagram = compose_graph_file("src/yaml/data/bool/and.yaml"))
#     nand_diagram = compose_graph_file("src/yaml/data/bool/nand.yaml"))
#     e = and_diagram# @ not_diagram @ nand_diagram
#     e = compose_entry(bool_diagram.to_hypergraph(), e.to_hypergraph())
#     e = compose_entry(e, bool_diagram.to_hypergraph()[::-1])
#     # e = compose_entry(e, bool_diagram.to_hypergraph()[::-1])
#     e.draw()

# def test_bool_and():
#     bool_diagram = compose_graph_file("src/yaml/data/bool.yaml"))
#     bool_and_diagram = compose_graph_file("src/yaml/data/bool/and.yaml"))
#     d = bool_diagram#compose_entry(bool_diagram.to_hypergraph(), bool_and_diagram.to_hypergraph())
#     # TyToBool = Functor(ob=lambda x: b if x == Ty("") else x, ar=lambda x: x)
#     # d.draw()
#     # d = TyToBool(d)
#     # d.draw()
#     and_boxes = {
#         Box("and", bn.dom, bn.cod): box_to_interface(bn)
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
