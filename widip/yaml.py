from discopy import symmetric, monoidal


Node = symmetric.Ty("")

class Scalar(symmetric.Box):
    def __init__(self, tag, value, dom=None, cod=None):
        if dom is None:
            dom = Node if tag else symmetric.Ty()
        if cod is None:
            cod = Node
        
        super().__init__("Scalar", dom, cod)
        self.tag, self.value = tag, value

class Label(symmetric.Box):
    def __init__(self, name):
        super().__init__(name, symmetric.Ty(), symmetric.Ty())

class Sequence(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside, dom=None, cod=None, n=1, tag=""):
        if tag:
            inside = inside @ Label(tag)
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)
        self.tag = tag
        self.n = n

class Mapping(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside, dom=None, cod=None, tag=""):
        if tag:
            inside = inside @ Label(tag)
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)
        self.tag = tag

class Anchor(monoidal.Bubble, symmetric.Box):
    def __init__(self, name, inside):
        super().__init__(inside, dom=inside.dom, cod=inside.cod)
        self.name = name

class Alias(symmetric.Box):
    def __init__(self, name, dom=None, cod=None):
        if dom is None: dom = Node
        if cod is None: cod = Node
        super().__init__(name, dom, cod)

class Copy(symmetric.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Copy({x}, {n})", x, x ** n)
        self.n = n

class Merge(symmetric.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Merge({x}, {n})", x ** n, x)
        self.n = n

class Discard(symmetric.Box):
    def __init__(self, x):
        super().__init__(f"Discard({x})", x, symmetric.Ty())

class Swap(symmetric.Swap):
    def __init__(self, x, y):
        super().__init__(x, y)

Yaml = symmetric.Category()
