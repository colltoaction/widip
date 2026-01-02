import contextvars
from typing import Any
from discopy import closed


class Node(closed.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)

class Scalar(closed.Box):
    def __init__(self, tag, value):
        dom, cod = closed.Ty(""), closed.Ty("")
        name = value if not tag else f"{tag}"
        closed.Box.__init__(self, "Scalar", dom, cod, drawing_name=name)
        self._tag, self._value = tag, value

    @property
    def tag(self):
        return self._tag

    @property
    def value(self):
        return self._value

class Sequence(closed.Box):
    def __init__(self, inside, dom=None, cod=None, n=None, tag=""):
        if tag:
            dom = dom or closed.Ty("")
            cod = cod or closed.Ty("")
        if dom is None: dom = inside.dom if hasattr(inside, "dom") else closed.Ty("")
        if cod is None: cod = inside.cod if hasattr(inside, "cod") else closed.Ty("")

        self.n = n
        self.tag = tag
        closed.Box.__init__(self, "Sequence", dom, cod)
        self.args = (inside, )

class Mapping(closed.Box):
    def __init__(self, inside, dom=None, cod=None, tag=""):
        if tag:
            dom = dom or closed.Ty("")
            cod = cod or closed.Ty("")
        if dom is None: dom = inside.dom if hasattr(inside, "dom") else closed.Ty("")
        if cod is None: cod = inside.cod if hasattr(inside, "cod") else closed.Ty("")
        self.tag = tag
        name = f"!{tag}" if tag else "Mapping"
        closed.Box.__init__(self, "Mapping", dom, cod, drawing_name=name)
        self.args = (inside, )

RECURSION_REGISTRY: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("recursion", default={})

class Anchor(closed.Box):
    def __init__(self, name, inside):
        closed.Box.__init__(self, name, inside.dom, inside.cod)
        self.name = name
        self.args = (inside, )

class Alias(closed.Box):
    def __init__(self, name, dom=None, cod=None):
        if dom is None: dom = closed.Ty("")
        if cod is None: cod = closed.Ty("")
        super().__init__(name, dom, cod)

Yaml = closed.Category()

# TODO remove closed structure from yaml and loader
# and move it to computer
def get_exps_bases(cod):
    exps = closed.Ty().tensor(*[x.inside[0].exponent for x in cod])
    bases = closed.Ty().tensor(*[x.inside[0].base for x in cod])
    return exps, bases
