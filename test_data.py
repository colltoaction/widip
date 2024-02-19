import pathlib
import yaml
from discopy.frobenius import Box, Ty, Spider, Diagram, Id, Functor, Category, Hypergraph as H
from discopy import python

from files import compose_graph_file
from loader import compose_entry

b, t, f = Ty("bool"), Ty("true"), Ty("false")
# not_bool = Box("not", b, b)
not_true = Box("not", t, b)
not_false = Box("not", f, b)
t_box = Box("true", Ty(), b)
f_box = Box("false", Ty(), b)


def test_bool_not():
    bool_not_diagram = compose_graph_file(pathlib.Path("src/yaml/data/bool/not.yaml"))
    not_boxes = {Box("not", bn.dom, b): Id(bn.cod) for bn in bool_not_diagram.to_hypergraph().boxes}
    bool_not_functor = Functor(
        ob=lambda x: x,
        ar=lambda bd: not_boxes.get(bd, bd))
    assert bool_not_functor(not_true) == Id(f)
    assert bool_not_functor(not_false) == Id(t)

def test_bool_and():
    bool_diagram = compose_graph_file(pathlib.Path("src/yaml/data/bool.yaml"))
    bool_and_diagram = compose_graph_file(pathlib.Path("src/yaml/data/bool/and.yaml"))
    d = compose_entry(bool_diagram.to_hypergraph(), bool_and_diagram.to_hypergraph())
    and_boxes = {
        Box("and", bn.dom, b):
            (H.spiders(1, 0, bn.dom) >> H.spiders(0, 1, bn.cod)).to_diagram()
        for bn in d.boxes}
    bool_and_functor = Functor(
        ob=lambda x: x,
        ar=lambda bd: and_boxes.get(bd, bd))
    assert bool_and_functor(
        (Box("and", t @ f, b) @ Box("and", t @ f, b)) >> Id(b @ b))
    assert bool_and_functor(Box("and", t @ f, b)) == Id(f)
    assert bool_and_functor(Box("and", f @ t, b)) == Id(f)
    assert bool_and_functor(Box("and", f @ f, b)) == Id(f)
    assert bool_and_functor(Box("and", t @ t, b)) == Id(t)
