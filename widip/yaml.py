from discopy import closed
from .computer import Data, Sequential, Pair, Concurrent, Computation, Program

class Node(closed.Box):
    pass

class Scalar(Node):
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

        dom = closed.Ty(value) if value else closed.Ty()
        if tag:
            cod = closed.Ty(tag) >> closed.Ty(tag)
        else:
            cod = closed.Ty() >> closed.Ty(value)

        super().__init__("Scalar", dom, cod)

class Sequence(Node):
    def __init__(self, dom, cod, n=2):
        super().__init__("Sequence", dom, cod)
        self.n = n

class Mapping(Node):
    def __init__(self, dom, cod):
        super().__init__("Mapping", dom, cod)


Yaml = closed.Category(closed.Ty, closed.Box)

def yaml_to_shell_box(ar):
    if isinstance(ar, Scalar):
        if ar.tag:
            return Program(ar.tag, dom=ar.dom, cod=ar.cod).uncurry()
        return Data(ar.dom, ar.cod)
    if isinstance(ar, Sequence):
        if ar.n == 2:
            return Pair(ar.dom, ar.cod)
        return Sequential(ar.dom, ar.cod)
    if isinstance(ar, Mapping):
        return Concurrent(ar.dom, ar.cod)
    return ar

class YamlCompiler(closed.Functor):
    def __init__(self):
        super().__init__(
            ob=lambda x: x,
            ar=yaml_to_shell_box,
            dom=Yaml,
            cod=Computation
        )

YAML_COMPILER = YamlCompiler()
