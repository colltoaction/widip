from discopy import closed, monoidal
import functools
import operator

Language = closed.Ty("ℙ")  # ℙ is the type of programs/processes
Language2 = Language @ Language  # Tensor product for binary operations

class Data(closed.Box):
    def __init__(self, name, dom=None, cod=None):
        # Default to Language type for categorical composition
        if dom is None: dom = Language
        if cod is None: cod = Language
        super().__init__(name, dom, cod)

class Program(closed.Box):
    def __init__(self, name, args=None, dom=None, cod=None):
        # Default to Language type for categorical composition
        if dom is None: dom = Language
        if cod is None: cod = Language
        super().__init__(name, dom, cod)
        self.args = args or []

class Partial(closed.Box):
    def __init__(self, name, dom=None, cod=None):
        # Ensure the name is a string to satisfy DisCoPy's expectations
        name = str(name)
        super().__init__(name, dom or Language, cod or Language)

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
    def __init__(self, x=None, n=2):
        x = x or Language
        super().__init__(f"Copy({x}, {n})", x, x ** n)
        self.n = n

class Merge(monoidal.Box):
    def __init__(self, x=None, n=2):
        x = x or Language
        super().__init__(f"Merge({x}, {n})", x ** n, x)
        self.n = n

class Discard(monoidal.Box):
    def __init__(self, x=None):
        x = x or Language
        super().__init__(f"Discard({x})", x, monoidal.Ty())

class Computation:
    # Stub for Computation category
    pass

class Titi:
    read_stdin = Program("read_stdin")
    printer = Program("print")
