from discopy import monoidal


# TODO node class is unnecessary
class Node(monoidal.Box):
    def __init__(self, name, dom, cod, args=None):
        self.args = args
        super().__init__(name, dom, cod)

class Scalar(monoidal.Box):
    def __init__(self, tag, value):
        self._tag = tag
        self._value = value
        dom = monoidal.Ty()
        cod = monoidal.Ty()
        super().__init__("Scalar", dom, cod)

    @property
    def tag(self):
        return self._tag

    @property
    def value(self):
        return self._value

class Sequence(monoidal.Bubble):
    def __init__(self, inside, dom=None, cod=None, n=None):
        if dom is None:
            dom = inside.dom

        if cod is None:
            # We keep the logical codimension as monoidal.Ty
            # Compilation will handle the transformation to closed.Ty
            cod = inside.cod

        self.n = n if n is not None else len(inside.cod)
        super().__init__(inside, dom=dom, cod=cod)
        # Change method to bypass Functor's default bubble handling
        self.method = "sequence_bubble"

class Mapping(monoidal.Bubble):
    def __init__(self, inside, dom=None, cod=None):
        if dom is None:
            dom = inside.dom
        if cod is None:
            cod = inside.cod
        super().__init__(inside, dom=dom, cod=cod)
        self.method = "mapping_bubble"

class Anchor(monoidal.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)

class Alias(monoidal.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)


Yaml = monoidal.Category()
