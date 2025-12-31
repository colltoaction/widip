from discopy import closed, monoidal


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

class Sequence(monoidal.Bubble, closed.Box):
    def __init__(self, inside, dom=None, cod=None, n=None):
        if dom is None:
            dom = inside.dom

        if cod is None:
            # If n=2 is explicitly requested, use Pair logic (K -> V)
            # Otherwise use Tuple logic (all inputs -> all outputs)
            if n == 2:
                mid = len(inside.cod) // 2
                exps, _ = get_exps_bases(inside.cod[:mid])
                _, bases = get_exps_bases(inside.cod[mid:])
                cod = exps >> bases
            else:
                exps, bases = get_exps_bases(inside.cod)
                cod = exps >> bases

        self.n = n if n is not None else len(inside.cod)
        super().__init__(inside, dom=dom, cod=cod)
        # Change method to bypass Functor's default bubble handling
        self.method = "sequence_bubble"

class Mapping(monoidal.Bubble, closed.Box):
    def __init__(self, inside, dom=None, cod=None):
        if dom is None:
            dom = inside.dom
        if cod is None:
            exps, bases = get_exps_bases(inside.cod)
            cod = bases << exps
        super().__init__(inside, dom=dom, cod=cod)
        self.method = "mapping_bubble"

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
