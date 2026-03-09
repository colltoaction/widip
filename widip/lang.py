"""Textbook compilation transformations for the Run language."""

from discopy import closed, markov, monoidal

from . import computer


P = computer.ProgramTy()

class Partial(computer.Box, monoidal.Bubble):
    """
    Sec. 2.2.2. []:P×A⊸P
    A partial evaluator is a (P×Y)-indexed program satisfying {[Γ]y}a = {Γ}(y,a).
    X=P×Y and g:P×Y×A→B
    """
    def __init__(self, box, Y):
        self.box, self.Y = box, Y
        arg = (
            box @ Y @ box.dom >> 
            computer.Box("[]", P @ Y, P) @ box.dom >>
            computer.Eval(box.dom, box.cod))
        monoidal.Bubble.__init__(self, arg, dom=box.dom @ Y @ box.dom, cod=box.cod)
        # self.box = box if isinstance(box, computer.Ty) else computer.Ty(box)
        # computer.Box.__init__(self, "[]", P @ box.dom, P)

    def specialize(self):
        """Fig. 2.5: compile partial-evaluator box as operator + eval."""
        return self.box @ self.Y @ self.box.dom >> computer.Eval(self.Y @ self.box.dom, self.box.cod)


class Sequential(computer.Box, monoidal.Bubble):
    """
    Sec. 2.2.3. (;)_ABC:P×P⊸P
    A -{F;G}→ C = A -{F}→ B -{G}→ C
    """
    def __init__(self, f, g):
        self.f, self.g = f, g
        A, C = f.dom, g.cod
        arg = (
            f @ g @ A
            >> computer.Box("(;)", P @ P, P) @ A
            >> computer.Eval(A, C))
        monoidal.Bubble.__init__(self, arg, dom=arg.dom, draw_vertically=True)
        # computer.Box.__init__(self, "(;)", P @ P, P)

    def specialize(self):
        A, B, C = self.f.dom, self.f.cod, self.g.cod
        F = computer.Eval(A, B)
        G = computer.Eval(B, C)
        # TODO 
        return self.f @ self.g @ A >> P @ F >> G


class Parallel(computer.Box, monoidal.Bubble):
    """
    Sec. 2.2.3. (||)_AUBV:P×P⊸P
    A×U -{F||H}→ B×V = A -{F}→ B × U-{T}→ V
    """
    def __init__(self, f, g):
        self.f, self.g = f, g
        A, C = f.dom, g.cod
        arg = (
            f @ g @ A
            >> computer.Box("(||)", P @ P, P) @ A
            >> computer.Eval(A, C))
        monoidal.Bubble.__init__(self, arg, dom=arg.dom, draw_vertically=True)

    def specialize(self):
        A, U, B, V = self.f.dom, self.g.dom, self.f.cod, self.g.cod
        first = computer.Eval(A, B)
        second = computer.Eval(U, V)
        # TODO 
        swap = computer.Swap(P, A)
        return self.f @ self.g @ A @ U >> P @ swap @ U >> first @ second


class Data(computer.Box, monoidal.Bubble):
    """
    Eq. 2.6. ⌜−⌝ : A⊸P
    {}: P-→→A
    ⌜a⌝: P
    {⌜a⌝} = a
    """
    def __init__(self, A):
        self.A = A if isinstance(A, computer.Ty) else computer.Ty(A)
        args = (
            computer.Box("⌜−⌝", P, self.A),
            computer.Eval(computer.Ty(), self.A))
        monoidal.Bubble.__init__(self, *args, dom=P, cod=self.A)
        # computer.Box.__init__(self, "⌜−⌝", P, self.A)

    def specialize(self):
        """Eq. 2.8: compile quoted data using idempotent quote/eval structure."""
        return computer.Id(self.A)



class Compile(closed.Functor, markov.Functor):
    """Pure diagram compilation of custom boxes into closed+markov structure."""

    dom = computer.Category()
    cod = computer.Category()

    def __init__(self):
        super().__init__(ob=lambda ob: ob, ar=self.ar_map)

    def __call__(self, box):
        if isinstance(box, (Sequential, Parallel, Partial, Data)):
            return box.specialize()
        return box

    def ar_map(self, box):
        assert not isinstance(box, computer.Box)
        return box


### TODO
### recover equations below

def run(G: computer.Diagram, A: computer.Ty, B: computer.Ty):
    """Eq. 2.15: an X-natural family of surjections C(X × A, B) --→ C•(X,P) for each pair of computer.types A, B."""
    del G
    return computer.Eval(A, B)


def eval_f(G: computer.Diagram):
    """Eq. 2.15: an X-natural family of surjections C(X × A, B) --→ C•(X,P) for each pair of computer.types A, B."""
    return computer.Eval(G.dom, G.cod)


def parametrize(g: computer.Diagram):
    """
    Eq. 2.2: an X-parametrized program, presented as a cartesian function G:X⊸P that evaluates to g.
    g(x, a) = {Gx}a.
    """
    G = g.curry(left=False)
    A = g.dom[1:]
    return G >> computer.Eval(G.cod @ A >> g.cod)


def reparametrize(g: computer.Diagram, s: computer.Diagram):
    """
    Fig. 2.3 Reparametring x along s:Y⊸X leads to the family g_s(y):A→B parametrized by y:Y and implemented by the reparametrization Gs=(Y -s⊸ X -G⊸ P) of the program G for g.
    """
    A = g.dom[1:]
    Gs = s @ A >> g.curry(left=False)
    return Gs >> computer.Eval(Gs.cod @ A >> g.cod)


def substitute(g: computer.Diagram, s: computer.Diagram):
    """
    Fig. 2.3 Substituting for a along t:C→A leads to the familiy h_X=(C -t→ A -g_x→ B), still parametrized over X, but requiring a program H:X⊸P) of the program G for g.
    """
    A = g.dom[1:]
    Gs = s @ A >> g.curry(left=False)
    return Gs >> computer.Eval(Gs.cod @ A >> g.cod)


def constant_a(f: computer.Diagram):
    """Sec. 2.2.1.3 a) f:I×A→B. f(a) = {Φ_a}()."""
    return f.curry(0, left=False)


def constant_b(f: computer.Diagram):
    """Sec. 2.2.1.3 b) f: A×I→B. f(a) = {F}(a)."""
    return f.curry(1, left=False)
