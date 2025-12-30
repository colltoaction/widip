from discopy import closed

class Node(closed.Box):
    pass

class Scalar(Node):
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

        dom = closed.Ty(value) if value else closed.Ty()
        if tag:
            cod = closed.Ty(tag) >> closed.Ty(tag)
        else:
            cod = closed.Ty() >> closed.Ty(value)

        super().__init__("Scalar", dom, cod)

class Sequence(Node):
    def __init__(self, dom, cod, n=2):
        super().__init__("Sequence", dom, cod)
        self.n = n

class Mapping(Node):
    def __init__(self, dom, cod):
        super().__init__("Mapping", dom, cod)


Yaml = closed.Category(closed.Ty, closed.Box)
