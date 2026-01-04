from discopy import closed, monoidal
import functools
import operator

Language = closed.Ty("Language")
Language2 = closed.Ty("Language2")

class Data(closed.Box):
    def __init__(self, name, dom=None, cod=None):
        if dom is None: dom = closed.Ty()
        if cod is None: cod = closed.Ty()
        super().__init__(name, dom, cod)

class Program(closed.Box):
    def __init__(self, name, args=None, dom=None, cod=None):
        if dom is None: dom = closed.Ty()
        if cod is None: cod = closed.Ty()
        super().__init__(name, dom, cod)
        self.args = args or []

class Partial(closed.Box):
    def __init__(self, name, dom=None, cod=None):
        super().__init__(name, dom or closed.Ty(), cod or closed.Ty())

def eval_diagram(tuples):
    """
    monoid
    """
    if not tuples:
        return ()
    return functools.reduce(operator.add, tuples, ())

def eval_python(code):
    """
    functor
    """
    return eval(code)

service_map = {}

class Copy(monoidal.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Copy({x}, {n})", x, x ** n)
        self.n = n

class Merge(monoidal.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Merge({x}, {n})", x ** n, x)
        self.n = n

class Discard(monoidal.Box):
    def __init__(self, x):
        super().__init__(f"Discard({x})", x, monoidal.Ty())

class Computation:
    # Stub for Computation category
    pass

class Titi:
    read_stdin = Program("read_stdin")
    printer = Program("print")
