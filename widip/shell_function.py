from discopy import python


class ShellFunction(python.Function):
    """"""
    # TODO re-enable type checking
    type_checking = False

    def then(self, other):
        f = python.Function.then(self, other)
        return ShellFunction(f.inside, f.dom, f.cod)

    def tensor(self, other):
        f = python.Function.tensor(self, other)
        return ShellFunction(f.inside, f.dom, f.cod)

    @staticmethod
    def id(dom):
        f = python.Function.id(dom)
        return ShellFunction(f.inside, f.dom, f.cod)

    @staticmethod
    def swap(x, y):
        f = python.Function.swap(x, y)
        return ShellFunction(f.inside, f.dom, f.cod)

    @staticmethod
    def copy(x, n=2):
        f = python.Function.copy(x, n)
        return ShellFunction(f.inside, f.dom, f.cod)

    @staticmethod
    def discard(dom):
        f = python.Function.discard(dom)
        return ShellFunction(f.inside, f.dom, f.cod)

    @staticmethod
    def ev(base, exponent, left=True):
        f = python.Function.ev(base, exponent, left)
        return ShellFunction(f.inside, f.dom, f.cod)

    def curry(self, n=1, left=True):
        f = super(ShellFunction, self).curry(n, left)
        return ShellFunction(f.inside, f.dom, f.cod)

    def uncurry(self, left=True):
        f = super(ShellFunction, self).uncurry(left)
        return ShellFunction(f.inside, f.dom, f.cod)

    def fix(self, n=1):
        f = super(ShellFunction, self).fix(n)
        return ShellFunction(f.inside, f.dom, f.cod)

    def trace(self, n=1, left=False):
        f = super(ShellFunction, self).trace(n, left)
        return ShellFunction(f.inside, f.dom, f.cod)
