import pathlib
from discopy.frobenius import Box, Ty, Diagram, Id, Spider

from bin.py.files import file_diagram

def test_crack_then_mix():
    white = Ty('white')
    yolk = Ty('yolk')
    egg = Ty('egg')
    crack = Box(name='crack', dom=egg, cod=white @ yolk)
    mix = Box('mix', white @ yolk, egg)
    crack_then_mix = crack >> mix

    t = file_diagram(pathlib.Path("examples/mascarpone/crack-then-mix.yaml").open())
    with Diagram.hypergraph_equality:
        assert t == crack_then_mix

def test_crack_then_beat():
    white = Ty('white')
    yolk = Ty('yolk')
    egg = Ty('egg')
    crack = Box(name='crack', dom=egg, cod=white @ yolk)
    sugar, yolky_paste = Ty('sugar'), Ty('yolky_paste')
    beat = Box('beat', yolk @ sugar, yolky_paste)
    crack_then_beat = crack @ sugar >> white @ beat

    t = file_diagram(pathlib.Path("examples/mascarpone/crack-then-beat.yaml").open())
    with Diagram.hypergraph_equality:
        assert t == crack_then_beat

def test_merge():
    white = Ty('white')
    merge = Box(name='merge', dom=white @ white, cod=white)

    t = file_diagram(pathlib.Path("examples/mascarpone/merge.yaml").open())
    with Diagram.hypergraph_equality:
        assert t == merge
