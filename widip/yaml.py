from discopy import closed
from .compiler import Data, Sequential, Concurrent

class Str(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("Str", dom, cod)

class Seq(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("Seq", dom, cod)

class Map(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("Map", dom, cod)

class Pair(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("Pair", dom, cod)

def yaml_to_shell_box(ar):
    if isinstance(ar, Str):
        return Data(ar.dom, ar.cod)
    if isinstance(ar, Seq):
        return Sequential(ar.dom, ar.cod)
    if isinstance(ar, Map):
        return Concurrent(ar.dom, ar.cod)
    if isinstance(ar, Pair):
        return Sequential(ar.dom, ar.cod)
    return ar

YAML_FUNCTOR = closed.Functor(
    ob=lambda x: x,
    ar=yaml_to_shell_box
)
