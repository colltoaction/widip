"""Textbook compilation transformations for the Run language."""

from discopy import closed, markov, monoidal

from . import computer


class Partial(computer.Box, monoidal.Bubble):
    """
    Sec. 2.2.2. []:P×A⊸P
    A partial evaluator is a (P×Y)-indexed program satisfying {[Γ]y}a = {Γ}(y,a).
    X=P×Y and g:P×Y×A→B
    """
    def __init__(self, gamma):
        self.gamma = gamma
        self.X, self.A = gamma.cod.exponent
        self.B = gamma.cod.base

        arg = (
            self.gamma @ self.X @ self.A
            >> computer.Box("[]", self.gamma.cod @ self.X, self.B << self.A) @ self.A
            >> computer.Eval(self.B << self.A)
        )

        monoidal.Bubble.__init__(self, arg, dom=arg.dom, cod=arg.cod)
        
    def specialize(self):
        """Fig. 2.5: compile partial-evaluator box as operator + eval."""
        return (
            self.gamma @ self.X @ self.A
            >> computer.Eval(self.B << self.X @ self.A)
        )


class Sequential(computer.Box, monoidal.Bubble):
    """
    Sec. 2.2.3. (;)_ABC:P×P⊸P
    A -{F;G}→ C = A -{F}→ B -{G}→ C
    """
    def __init__(self, F, G):
        self.F, self.G = F, G
        A = F.cod.exponent
        C = G.cod.base
        arg = (
            F @ G @ A
            >> computer.Box("(;)", F.cod @ G.cod, C << A) @ A
            >> computer.Eval(C << A)
        )

        monoidal.Bubble.__init__(self, arg, dom=arg.dom, draw_vertically=True)

    def specialize(self):
        F, G = self.F, self.G
        A = F.cod.exponent
        B = F.cod.base
        C = G.cod.base

        F_Eval = computer.Eval(B << A)
        G_Eval = computer.Eval(C << B)
        return G @ F @ A >> (C << B) @ F_Eval >> G_Eval


class Parallel(computer.Box, monoidal.Bubble):
    """
    Sec. 2.2.3. (||)_AUBV:P×P⊸P
    A×U -{F||H}→ B×V = A -{F}→ B × U-{T}→ V
    """
    def __init__(self, F, T):
        self.F, self.T = F, T
        A, B = F.cod.exponent, F.cod.base
        U, V = T.cod.exponent, T.cod.base
        arg = (
            A @ U @ F @ T
            >> A @ U @ computer.Box("(||)", F.cod @ T.cod, A @ U >> B @ V)
            >> computer.Eval(A @ U >> B @ V)
        )
        monoidal.Bubble.__init__(self, arg, dom=arg.dom, draw_vertically=True)

    def specialize(self):
        F, T = self.F, self.T
        A, B = F.cod.exponent, F.cod.base
        U, V = T.cod.exponent, T.cod.base

        first = computer.Eval(B << A)
        second = computer.Eval(V << U)
        swap = computer.Swap(V << U, A)
        return F @ T @ A @ U >> (B << A) @ swap @ U >> first @ second


class Data(computer.Box, monoidal.Bubble):
    """
    Eq. 2.6. ⌜−⌝ : A⊸P
    {}: P-→→A
    ⌜a⌝: P
    {⌜a⌝} = a
    """
    def __init__(self, A):
        self.A = A if isinstance(A, computer.Ty) else computer.Ty(A)
        arg = (
            computer.Box("⌜−⌝", self.A, computer.Ty() >> self.A) >>
            computer.Eval(computer.Ty() >> self.A))
        monoidal.Bubble.__init__(self, arg, dom=self.A, cod=self.A)
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
