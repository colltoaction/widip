from discopy import closed
from .computer import Data, Sequential, Concurrent, Computation

NODE = closed.Ty("Node")

class Node(closed.Box):
    def __init__(self, name, dom, cod=NODE, **params):
        super().__init__(name, dom, cod, **params)

class Scalar(Node):
    def __init__(self, value, tag=None):
        name = tag if tag else "Scalar"
        drawing_name = f"⌜{tag}⌝" if tag else (f"⌜{value}⌝" if value else "⌜−⌝")
        dom = closed.Ty(value) if value is not None else closed.Ty()
        super().__init__(name, dom, cod=NODE, drawing_name=drawing_name)

class Sequence(Node):
    def __init__(self, dom):
        super().__init__("Sequence", dom, NODE)

class Mapping(Node):
    def __init__(self, dom):
        super().__init__("Mapping", dom, NODE)


Yaml = closed.Category(closed.Ty, closed.Box)

def yaml_to_shell_box(ar):
    if isinstance(ar, Scalar):
        # Pass name, dom, cod, drawing_name.
        return Data(ar.name, ar.dom, ar.cod, drawing_name=ar.drawing_name)
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
