from discopy import closed


Node = closed.Ty("")

class Scalar(closed.Box):
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

        dom = closed.Ty(value) if value else closed.Ty()
        if tag:
            cod = closed.Ty(tag) >> closed.Ty(tag)
        else:
            cod = closed.Ty() >> closed.Ty(value)

        super().__init__("Scalar", dom, cod)

class Sequence(closed.Box):
    def __init__(self, dom, cod, n=2):
        super().__init__("Sequence", dom, cod)
        self.n = n

class Mapping(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("Mapping", dom, cod)

class Anchor(closed.Box):
    def __init__(self, name, dom, cod):
        self.name = name
        super().__init__("Anchor", dom, cod)

class Alias(closed.Box):
    def __init__(self, name, dom, cod):
        self.name = name
        super().__init__("Alias", dom, cod)

Yaml = closed.Category()
