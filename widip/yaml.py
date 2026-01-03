from discopy import traced, symmetric, monoidal


Node = symmetric.Ty("")

class Scalar(symmetric.Box):
    def __init__(self, tag, value, dom=None, cod=None):
        if dom is None:
            dom = Node if tag else symmetric.Ty()
        if cod is None:
            cod = Node
        
        super().__init__("Scalar", dom, cod)
        self.tag, self.value = tag, value

class Sequence(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside, dom=None, cod=None, n=1, tag=""):
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)
        self.tag = tag
        self.n = n

class Mapping(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside, dom=None, cod=None, tag=""):
        if dom is None:
            dom = Node if tag else inside.dom
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)
        self.tag = tag

# --- Recursion boxes (marked for traced semantics) ---

class Anchor(monoidal.Bubble, symmetric.Box):
    """Anchor defines a recursive loop point (traced semantics)."""
    draw_as_trace = True  # Mark for traced rendering
    def __init__(self, name, inside):
        super().__init__(inside, dom=inside.dom, cod=inside.cod)
        self.name = name

class Alias(symmetric.Box):
    """Alias references an anchor, creating a feedback loop (traced semantics)."""
    draw_as_trace = True  # Mark for traced rendering
    def __init__(self, name, dom=None, cod=None):
        if dom is None: dom = Node
        if cod is None: cod = Node
        super().__init__(name, dom, cod)

# --- Document structure ---

class Document(monoidal.Bubble, symmetric.Box):
    """YAML Document box - wraps root content."""
    def __init__(self, inside, dom=None, cod=None):
        if dom is None:
            dom = symmetric.Ty()
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)

class Stream(monoidal.Bubble, symmetric.Box):
    """YAML Stream box - wraps multiple documents."""
    def __init__(self, inside, dom=None, cod=None):
        if dom is None:
            dom = symmetric.Ty()
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)

Yaml = symmetric.Category()
