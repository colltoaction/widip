from discopy import closed


# TODO node class is unnecessary
class Node(closed.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)

class Scalar(closed.Box):
    def __init__(self, tag, value):
        dom = closed.Ty(value) if value else closed.Ty()
        cod = closed.Ty(tag) >> closed.Ty(tag) if tag else closed.Ty() >> closed.Ty(value)
        super().__init__("Scalar", dom, cod)

    @property
    def tag(self):
        if not self.cod or not self.cod[0].is_exp: return ""
        u = self.cod[0].inside[0]
        return u.base.name if u.base == u.exponent else ""

    @property
    def value(self):
        if self.dom: return self.dom[0].name
        if not self.cod or not self.cod[0].is_exp: return ""
        u = self.cod[0].inside[0]
        return u.base.name if not self.tag else ""

class Sequence(closed.Box):
    def __init__(self, dom, cod=None, n=2):
        if cod is None:
            if n == 2:
                mid = len(dom) // 2
                exps, _ = get_exps_bases(dom[:mid])
                _, bases = get_exps_bases(dom[mid:])
                cod = exps >> bases
            else:
                exps, bases = get_exps_bases(dom)
                cod = exps >> bases
        super().__init__("Sequence", dom, cod)

    @property
    def n(self):
        return len(self.dom)

class Mapping(closed.Box):
    def __init__(self, dom, cod=None):
        if cod is None:
            exps, bases = get_exps_bases(dom)
            cod = bases << exps
        super().__init__("Mapping", dom, cod)

class Anchor(closed.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)

class Alias(closed.Box):
    def __init__(self, name, dom, cod):
        super().__init__(name, dom, cod)

Yaml = closed.Category()

# TODO remove closed structure from yaml and loader
# and move it to computer
def get_exps_bases(cod):
    exps = closed.Ty().tensor(*[x.inside[0].exponent for x in cod])
    bases = closed.Ty().tensor(*[x.inside[0].base for x in cod])
    return exps, bases
