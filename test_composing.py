from discopy.frobenius import Box, Ty, Diagram, Id, Spider

from composing import glue_diagrams
from bin.py.files import files_f


def test_glue_diagrams():
    white = Ty('white')
    yolk = Ty('yolk')
    egg = Ty('egg')
    crack = Box(name='crack', dom=egg, cod=white @ yolk)
    sugar, yolky_paste = Ty('sugar'), Ty('yolky_paste')
    beat = Box('beat', yolk @ sugar, yolky_paste)

    file_box = Box("file://./examples/mascarpone/crack-then-beat.yaml", Ty(), Ty())
    crack_then_beat = files_f(file_box)
    with Diagram.hypergraph_equality:
        assert glue_diagrams(crack, beat) == crack_then_beat
