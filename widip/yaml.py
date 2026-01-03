from discopy import symmetric, monoidal


Node = symmetric.Ty("")

class Scalar(symmetric.Box):
    def __init__(self, tag, value, dom=None, cod=None):
        if dom is None:
            dom = Node if tag else symmetric.Ty()
        if cod is None:
            cod = Node
        name = value if not tag else f"{tag}"
        super().__init__("Scalar", dom, cod, drawing_name=name)
        self._tag, self._value = tag, value
        
        # Calculate box width using max line length split by "\n"
        lines = name.split('\n')
        self.drawing_width = max(len(l) for l in lines) if lines else 1
        
        # Visual styling - white background for readability
        if tag:
            # Tagged scalars (commands) - white boxes
            self.color = "white"
            self.draw_as_spider = False
        elif not name:
            # Empty scalars - small white dots
            self.draw_as_spider = True
            self.color = "white"
        else:
            # Data scalars - white boxes
            self.color = "white"
            self.draw_as_spider = False

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
        self.n = n
        # Sequences - black bubbles
        self.draw_as_spider = False
        self.color = "black"
        if tag:
            self.drawing_name = f"[{tag}]"

class Mapping(monoidal.Bubble):
    def __init__(self, inside, dom=None, cod=None, tag=""):
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)
        self.tag = tag
        self.tag = tag
        # Mappings - black bubbles
        self.draw_as_spider = False
        self.color = "black"
        if tag:
            self.drawing_name = f"{{{tag}}}"

class Anchor(monoidal.Bubble):
    def __init__(self, name, inside):
        super().__init__(inside, dom=inside.dom, cod=inside.cod)
        self.name = name
        # Anchors - blue bubbles
        self.draw_as_spider = False
        self.color = "blue"
        self.drawing_name = f"&{name}"

class Alias(symmetric.Box):
    def __init__(self, name, dom=None, cod=None):
        if dom is None: dom = Node
        if cod is None: cod = Node
        super().__init__(name, dom, cod)
        # Aliases - blue spiders
        self.draw_as_spider = True
        self.color = "blue"
        self.drawing_name = f"*{name}"

class Copy(symmetric.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Copy({x}, {n})", x, x ** n)
        self.n = n
        # Copy - green spider
        self.draw_as_spider = True
        self.drawing_name = ""
        self.color = "green"

class Merge(symmetric.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Merge({x}, {n})", x ** n, x)
        self.n = n
        # Merge - green box with label
        self.draw_as_spider = True
        self.drawing_name = f"⊗{n}" if n > 2 else "⊗"
        self.color = "green"

class Discard(symmetric.Box):
    def __init__(self, x):
        super().__init__(f"Discard({x})", x, symmetric.Ty())
        # Discard - red spider/dot
        self.draw_as_spider = True
        self.color = "red"
        # handle Ty() and Ty("")
        if x == symmetric.Ty() or x == Node:
            self.drawing_name = ""
        else:
            self.drawing_name = "×"

class Swap(symmetric.Swap):
    def __init__(self, x, y):
        super().__init__(x, y)
        # Swap - yellow crossing
        self.shape = "circle"
        self.draw_as_swap = True
        self.symmetric = True
        self.color = "yellow"

Yaml = symmetric.Category()
