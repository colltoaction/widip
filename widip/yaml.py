from discopy import closed
from .computer import Data, Sequential, Concurrent, Computation

class Node(closed.Box):
    pass

class Scalar(Node):
    def __init__(self, dom, cod):
        super().__init__("Scalar", dom, cod)

class Sequence(Node):
    def __init__(self, dom, cod):
        super().__init__("Sequence", dom, cod)

class Mapping(Node):
    def __init__(self, dom, cod):
        super().__init__("Mapping", dom, cod)


Yaml = closed.Category(closed.Ty, closed.Box)

def yaml_to_shell_box(ar):
    if isinstance(ar, Scalar):
        return Data(ar.dom, ar.cod)
    if isinstance(ar, Sequence):
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
