from discopy import monoidal


Node = monoidal.Ty("")

class Scalar(monoidal.Box):
    def __init__(self, tag, value, dom=None, cod=None):
        if dom is None:
            dom = Node if tag else monoidal.Ty()
        if cod is None:
            cod = Node
        name = value if not tag else f"{tag}"
        super().__init__("Scalar", dom, cod, drawing_name=name)
        self._tag, self._value = tag, value

    @property
    def tag(self):
        return self._tag

    @property
    def value(self):
        return self._value

class Sequence(monoidal.Bubble):
    def __init__(self, inside, dom=None, cod=None, n=None, tag=""):
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)
        self.tag = tag
        self.n = n

class Mapping(monoidal.Bubble):
    def __init__(self, inside, dom=None, cod=None, tag=""):
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)
        self.tag = tag

class Anchor(monoidal.Bubble):
    def __init__(self, name, inside):
        super().__init__(inside, dom=inside.dom, cod=inside.cod)
        self.name = name

class Alias(monoidal.Box):
    def __init__(self, name, dom=None, cod=None):
        if dom is None: dom = Node
        if cod is None: cod = Node
        super().__init__(name, dom, cod)

class Copy(monoidal.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Copy({x}, {n})", x, x ** n)
        self.n = n

class Merge(monoidal.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Merge({x}, {n})", x ** n, x)
        self.n = n

class Discard(monoidal.Box):
    def __init__(self, x):
        super().__init__(f"Discard({x})", x, monoidal.Ty())

class Swap(monoidal.Box):
    def __init__(self, x, y):
        super().__init__(f"Swap({x}, {y})", x @ y, y @ x)

Yaml = monoidal.Category()
