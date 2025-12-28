from discopy import closed
from .computer import Data, Sequential, Pair, Concurrent, Computation, Discard

class Node(closed.Box):
    pass

class Scalar(Node):
    def __init__(self, tag, v):
        self.tag = tag
        self.value = v
        if v and not isinstance(v, str) and hasattr(v, '__iter__'):
             flat_v = []
             def flatten(x):
                 if isinstance(x, str):
                     flat_v.append(x)
                 elif hasattr(x, '__iter__'):
                     for i in x:
                         flatten(i)
                 else:
                     flat_v.append(str(x))
             flatten(v)
             dom_v = closed.Ty(*flat_v)
        else:
             dom_v = closed.Ty(v) if v else closed.Ty()
        dom = closed.Ty(tag or "str") @ dom_v
        cod = closed.Ty(tag or "str") << closed.Ty(tag or "str")
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
        tag = ar.tag or "str"
        if len(ar.dom) >= 2:
            val_ty = ar.dom[1:]
            if tag != "str":
                return Discard(ar.dom[:1]) @ closed.Id(val_ty) >> closed.Box(tag, val_ty, ar.cod)
            return Discard(ar.dom[:1]) @ Data(val_ty, ar.cod)

        if tag != "str":
            return Discard(ar.dom) >> closed.Box(tag, closed.Ty(), ar.cod)
        return Discard(ar.dom) @ Data(closed.Ty(), ar.cod)
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
