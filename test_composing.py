import pathlib
from discopy.frobenius import Box, Ty, Diagram, Id, Spider

from composing import glue_diagrams
from files import file_diagram


def test_glue_diagrams():
    white = Ty('white')
    yolk = Ty('yolk')
    egg = Ty('egg')
    crack = Box(name='crack', dom=egg, cod=white @ yolk)
    sugar, yolky_paste = Ty('sugar'), Ty('yolky_paste')
    beat = Box('beat', yolk @ sugar, yolky_paste)

    crack_then_beat = file_diagram(pathlib.Path("examples/mascarpone/crack-then-beat.yaml").open())
    with Diagram.hypergraph_equality:
        assert glue_diagrams(crack, beat) == crack_then_beat
