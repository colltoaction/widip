import contextvars
from typing import Any
from discopy import closed, monoidal
from .computer import Language, Trace, Copy, Discard, Eval, Swap


class Node(closed.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)

    def to_closed(self):
        return self

class Scalar(closed.Box):
    def __init__(self, tag, value):
        dom, cod = Language, Language
        closed.Box.__init__(self, "Scalar", dom, cod)
        self._tag, self._value = tag, value

    @property
    def tag(self):
        return self._tag

    @property
    def value(self):
        return self._value

    def to_closed(self):
        from .compiler import Exec, Program, Data
        if self.tag == "exec":
            return Exec(self.dom, self.cod)
        if self.tag:
            # Tagged scalar: command name is tag, argument is value
            args = (self.value, ) if self.value else ()
            return Program(self.tag, args=args, dom=self.dom, cod=self.cod)
        return Data(self.dom, self.cod, self.value)

class Sequence(closed.Box):
    def __init__(self, inside, dom=None, cod=None, n=None, tag=""):
        if dom is None: dom = inside.dom if hasattr(inside, "dom") else Language
        if cod is None: cod = inside.cod if hasattr(inside, "cod") else Language

        self.n = n
        self.tag = tag
        closed.Box.__init__(self, "Sequence", dom, cod)
        self.args = (inside, )

    def to_closed(self):
        from .compiler import SHELL_COMPILER, Program, Language
        ob = SHELL_COMPILER(self.args[0])
        if self.tag:
            return Program(self.tag, args=(ob, ))
        return ob

class Mapping(closed.Box):
    def __init__(self, inside, dom=None, cod=None, tag=""):
        if dom is None: dom = inside.dom if hasattr(inside, "dom") else Language
        if cod is None: cod = inside.cod if hasattr(inside, "cod") else Language
        self.tag = tag
        closed.Box.__init__(self, "Mapping", dom, cod)
        self.args = (inside, )

    def to_closed(self):
        from .compiler import SHELL_COMPILER, Program, Language
        ob = SHELL_COMPILER(self.args[0])
        if self.tag:
            return Program(self.tag, args=(ob, ))
        return ob

RECURSION_REGISTRY: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("recursion", default={})

class Anchor(closed.Box):
    def __init__(self, name, inside):
        closed.Box.__init__(self, name, inside.dom, inside.cod)
        self.name = name
        self.args = (inside, )

    def to_closed(self):
        from .compiler import SHELL_COMPILER
        # Register the anchor for later lookup during execution
        anchors = RECURSION_REGISTRY.get().copy()
        anchors[self.name] = self.args[0]
        RECURSION_REGISTRY.set(anchors)
        return SHELL_COMPILER(self.args[0])

class Alias(closed.Box):
    def __init__(self, name, dom=None, cod=None):
        if dom is None: dom = Language
        if cod is None: cod = Language
        super().__init__(name, dom, cod)

    def to_closed(self):
        from .compiler import Program
        # Recursive call! Return a Program box with the anchor name.
        return Program(self.name, dom=self.dom, cod=self.cod)

Yaml = closed.Category()

# TODO remove closed structure from yaml and loader
# and move it to computer
def get_exps_bases(cod):
    exps = closed.Ty().tensor(*[x.inside[0].exponent for x in cod])
    bases = closed.Ty().tensor(*[x.inside[0].base for x in cod])
    return exps, bases
