from discopy import symmetric, monoidal


Node = symmetric.Ty("")

class Scalar(symmetric.Box):
    def __init__(self, tag, value, dom=None, cod=None):
        if dom is None:
            dom = Node if tag else symmetric.Ty()
        if cod is None:
            cod = Node
        
        name = f"{tag} {value}" if tag and value else (tag or value)
        super().__init__("Scalar", dom, cod, drawing_name=name)
        self._tag, self._value = tag, value
        
        self._tag, self._value = tag, value
        
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

class Label(symmetric.Box):
    def __init__(self, name):
        super().__init__(name, symmetric.Ty(), symmetric.Ty())
        self.draw_as_spider = False
        self.color = "white"
        self.drawing_name = name

class Sequence(monoidal.Bubble):
    def __init__(self, inside, dom=None, cod=None, n=1, tag=""):
        if tag:
            inside = inside @ Label(tag)
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        name = f"[{tag}]" if tag else ""
        super().__init__(inside, dom=dom, cod=cod, drawing_name=name)
        self.tag = tag
        self.n = n
        # Sequences - white bubbles
        self.draw_as_spider = False
        self.color = "white"
        if tag:
            self.name = name

class Mapping(monoidal.Bubble):
    def __init__(self, inside, dom=None, cod=None, tag=""):
        if tag:
            inside = inside @ Label(tag)
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        name = f"{{{tag}}}" if tag else ""
        super().__init__(inside, dom=dom, cod=cod, drawing_name=name)
        self.tag = tag
        # Mappings - white bubbles
        self.draw_as_spider = False
        self.color = "white"
        if tag:
            self.name = name

class Anchor(monoidal.Bubble):
    def __init__(self, name, inside):
        dname = f"&{name}"
        super().__init__(inside, dom=inside.dom, cod=inside.cod, drawing_name=dname)
        self.name = name
        # Anchors - blue bubbles
        self.draw_as_spider = False
        self.color = "blue"
        self.name = dname

class Alias(symmetric.Box):
    def __init__(self, name, dom=None, cod=None):
        if dom is None: dom = Node
        if cod is None: cod = Node
        super().__init__(name, dom, cod)
        # Aliases - blue boxes
        self.draw_as_spider = False
        self.color = "blue"
        self.drawing_name = f"*{name}"

class Copy(symmetric.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Copy({x}, {n})", x, x ** n)
        self.n = n
        # Copy - green spider
        self.draw_as_spider = True
        self.drawing_name = "Δ"
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
            self.color = "white"
        else:
            self.drawing_name = "×"
            self.color = "red" 

class Swap(symmetric.Swap):
    def __init__(self, x, y):
        super().__init__(x, y)
        # Swap - yellow crossing
        self.shape = "circle"
        self.draw_as_swap = True
        self.symmetric = True
        self.color = "yellow"

class Stream(monoidal.Bubble):
    def __init__(self, inside):
        super().__init__(inside, dom=inside.dom, cod=inside.cod, drawing_name="Stream")
        # Stream - white bubble
        self.draw_as_spider = False
        self.color = "white"
        self.name = "Stream"

Yaml = symmetric.Category()
