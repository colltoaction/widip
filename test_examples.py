import pathlib
from discopy.frobenius import Box, Ty, Diagram

from files import compose_graph_file

def test_crack_then_mix():
    white = Ty('white')
    yolk = Ty('yolk')
    egg = Ty('egg')
    crack = Box(name='crack', dom=egg, cod=white @ yolk)
    mix = Box('mix', white @ yolk, egg)
    crack_then_mix = crack >> mix

    t = compose_graph_file(pathlib.Path("examples/crack-then-mix.yaml"))
    with Diagram.hypergraph_equality:
        assert t == crack_then_mix
