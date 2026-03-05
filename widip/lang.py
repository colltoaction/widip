"""The Run language category."""

from discopy import symmetric, cat
from discopy.utils import factory


class ProgramOb(cat.Ob):
    """Internal object tag for the distinguished program type."""


class Box(symmetric.Box):
    """"""


class Copy(Box):
    """
    1.2, 2.5.1 a) Copying data service: A⊸A×A.
    """
    def __init__(self, A):
        Box.__init__(self, "∆", A, A @ A)

class Delete(Box):
    """
    1.2, 2.5.1 a) Deleting data service: A⊸I.
    """
    def __init__(self, A):
        Box.__init__(self, "⊸", A, Ty())

class Swap(Box, symmetric.Swap):
    """1.2"""


class Eval(Box):
    """
    2.2.1.1 
    2.5.1 c) Program evaluator {}:P×A→B
    """
    def __init__(self, A, B):
        self.A, self.B = A, B
        Box.__init__(self, "{}", ProgramTy() @ A, B)

    def partial(self):
        """Figure 2.5: Partial evaluators are indexed program"""
        Y = self.A[:1]
        return Partial(Y) >> Eval(Y, self.B)

class Partial(Box):
    """
    Fig. 2.2.2. []:P×A⊸P
    X=P×Y and g:P×Y×A→B
    """
    def __init__(self, X):
        self.X = X
        Box.__init__(self, "[]", ProgramTy() @ X, ProgramTy())

class Sequential(Box):
    """Sec. 2.2.3."""
    def __init__(self):
        Box.__init__(self, "(;)", ProgramTy() @ ProgramTy(), ProgramTy())

class Parallel(Box):
    """Sec. 2.2.3."""
    def __init__(self):
        Box.__init__(self, "(||)", ProgramTy() @ ProgramTy(), ProgramTy())

class Data(Box):
    """Eq. 2.6."""
    def __init__(self, A):
        self.A = A
        Box.__init__(self, "⌜−⌝", ProgramTy(), A)

    def idempotent(self):
        """Eq. 2.7."""
        return Eval(Ty(), self.A)

@factory
class Ty(symmetric.Ty):
    def tensor(self, *others):
        # Preserve distinguished subtypes when tensoring with the monoidal unit.
        if len(others) == 1:
            other = others[0]
            if len(self) == 0:
                return other
            if len(other) == 0:
                return self
        return symmetric.Ty.tensor(self, *others)

    # 2.5.1 b) Distinguished program type has decidable equality.
    def __eq__(self, other):
        return not isinstance(other, ProgramTy) \
            and symmetric.Ty.__eq__(self, other)

class ProgramTy(Ty):
    """2.5.1 b) Distinguished type P of programs with a decidable equality predicate"""
    def __init__(self):
        Ty.__init__(self, ProgramOb())

    def __eq__(self, other):
        return isinstance(other, ProgramTy)


@factory
class Diagram(symmetric.Diagram):
    ty_factory = Ty


class Category(symmetric.Category):
    """2.5.1: A monoidal computer is a (symmetric, strict) monoidal category"""
    ob, ar = Ty, Diagram

class CartesianCategory(cat.Category):
    """
    Eq 1.10: The data services in a monoidal category C. Keeping all of the objects of C but restricting to the cartesian functions yields the category C•.
    A category is cartesian if it has the final object and the cartesian products A×B for all types A,B, as in (1.7-1.8) and (1.13). It is closed with respect to the cartesian products if it has the exponents B^A, as in (1.15).
    In Ch. 7, we explore a version suitable for programming: the program closed categories.
    """

def Id(x=Ty()):
    """Identity diagram over widip.lang.Ty (defaults to Ty())."""
    return symmetric.Diagram.id(x)

def run(G: Diagram, A: Ty, B: Ty):
    """Eq. 2.15: an X-natural family of surjections C(X × A, B) --→ C•(X,P) for each pair of types A, B"""
    return Eval(A, B)

def eval_f(G: Diagram):
    """Eq. 2.15: an X-natural family of surjections C(X × A, B) --→ C•(X,P) for each pair of types A, B"""
    return Eval(G.dom, G.cod)

def parametrize(g: Diagram):
    """
    Eq. 2.2: an X-parametrized program, presented as a cartesian function G:X⊸P that evaluates to g.
    g(x, a) = {Gx}a.
    """
    G = g.curry(left=False)
    return G >> Eval(G.cod @ g.dom[1:] >> g.cod)

def reparametrize(g: Diagram, s: Diagram):
    """
    Fig. 2.3 Reparametring x along s:Y⊸X leads to the family g_s(y):A→B parametrized by y:Y and implemented by the reparametrization Gs=(Y -s⊸ X -G⊸ P) of the program G for g.
    """
    A = g.dom[1:]
    Gs = s @ A >> g.curry(left=False)
    return Gs >> Eval(Gs.cod @ A >> g.cod)

def substitute(g: Diagram, s: Diagram):
    """
    Fig. 2.3 Substituting for a along t:C→A leads to the familiy h_X=(C -t→ A -g_x→ B), still parametrized over X, but requiring a program H:X⊸P) of the program G for g.
    """
    A = g.dom[1:]
    Gs = s @ A >> g.curry(left=False)
    return Gs >> Eval(Gs.cod @ A >> g.cod)

def constant_a(f: Diagram):
    """Sec. 2.2.1.3 a) f:I×A→B. f(a) = {Φ_a}()"""
    return f.curry(0, left=False)

def constant_b(f: Diagram):
    """Sec. 2.2.1.3 b) f: A×I→B. f(a) = {F}(a)"""
    return f.curry(1, left=False)

###
# Ch. 7: Stateful computing
###

def process():
    """
    Eq 7.1: A process q: X×A→X×B = <q⊲,q⊙>
    q⊙_x(a): A→B input-output mapping.
    q⊲_x(a): A→X state update mapping.
    """

def program_execution(G: Diagram, A: Ty, B: Ty):
    """Eq. 7.3: {{}}^B_A = {}^P×B_A: P×A→P×B"""
    return Eval(A, B)
