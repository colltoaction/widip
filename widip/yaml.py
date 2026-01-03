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
        
        # if empty draw as box
        if not name:
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
        self.draw_as_spider = True
        self.color = "black"

class Mapping(monoidal.Bubble):
    def __init__(self, inside, dom=None, cod=None, tag=""):
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)
        self.tag = tag
        self.draw_as_spider = True
        self.color = "black"

class Anchor(monoidal.Bubble):
    def __init__(self, name, inside):
        super().__init__(inside, dom=inside.dom, cod=inside.cod)
        self.name = name
        self.draw_as_spider = True
        self.color = "black"

class Alias(symmetric.Box):
    def __init__(self, name, dom=None, cod=None):
        if dom is None: dom = Node
        if cod is None: cod = Node
        super().__init__(name, dom, cod)
        self.draw_as_spider = True
        self.color = "black"

class Copy(symmetric.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Copy({x}, {n})", x, x ** n)
        self.n = n
        self.draw_as_spider = True
        self.drawing_name = ""
        self.color = "black"

class Merge(symmetric.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Merge({x}, {n})", x ** n, x)
        self.n = n
        # draw as box (requested L70-76)
        self.draw_as_spider = False
        # display tag in merge box
        self.drawing_name = f"Merge({x}, {n})"

class Discard(symmetric.Box):
    def __init__(self, x):
        super().__init__(f"Discard({x})", x, symmetric.Ty())
        self.draw_as_spider = True
        # handle Ty() and Ty("")
        if x == symmetric.Ty() or x == Node:
            self.drawing_name = ""
        else:
            self.drawing_name = str(x)
        self.color = "black"

class Swap(symmetric.Swap):
    def __init__(self, x, y):
        super().__init__(x, y)
        # draw as squares (requested L71-73)
        self.shape = "square"
        self.draw_as_swap = True
        self.symmetric = True

Yaml = symmetric.Category()
