"""Textbook compilation transformations for the Run language."""

from discopy import closed, markov, monoidal

from . import computer


def compile_uncurry_sequential(box: computer.Uncurry):
    """Eq. 2.7: compile sequential `Uncurry` as closed Curry/Eval form."""
    operator = closed.Curry(box.arg, n=len(box.dom), left=True)
    return (operator @ box.dom) >> closed.Eval(operator.cod)


def compile_uncurry_parallel(box: computer.Uncurry):
    """Eq. 2.7: compile parallel `Uncurry` as closed Curry/Eval form."""
    operator = closed.Curry(box.arg, n=len(box.dom), left=True)
    return (operator @ box.dom) >> closed.Eval(operator.cod)


def compile_data_idempotent(box: computer.Data):
    """Eq. 2.8: compile quoted data using idempotent quote/eval structure."""
    source = box.bubble(dom=computer.Ty(), cod=box.cod)
    operator = closed.Curry(source, n=0, left=True)
    return (operator @ computer.Ty()) >> closed.Eval(operator.cod)


def compile_partial_evaluator(box: computer.Partial):
    """Fig. 2.5: compile partial-evaluator box as operator + eval."""
    source = box.bubble(dom=box.dom, cod=box.cod)
    operator = closed.Curry(source, n=len(box.dom), left=True)
    return (operator @ box.dom) >> closed.Eval(operator.cod)


class Compile(closed.Functor, markov.Functor):
    """Pure diagram compilation of custom boxes into closed+markov structure."""

    dom = computer.Category()
    cod = computer.Category()

    def __init__(self):
        super().__init__(ob=lambda ob: ob, ar=self.ar_map)

    def ar_map(self, box):
        if isinstance(box, (computer.Sequential, computer.Parallel)):
            source = box.bubble(dom=box.dom, cod=box.cod)
            operator = closed.Curry(source, n=len(box.dom), left=True)
            return (operator @ box.dom) >> closed.Eval(operator.cod)
        if isinstance(box, computer.Partial):
            return compile_partial_evaluator(box)
        if isinstance(box, computer.Data):
            return compile_data_idempotent(box)
        if isinstance(box, computer.Uncurry):
            inner = box.arg
            while isinstance(inner, monoidal.Bubble) and inner.name == "":
                inner = inner.arg
            if isinstance(inner, computer.Sequential):
                return compile_uncurry_sequential(box)
            if isinstance(inner, computer.Parallel):
                return compile_uncurry_parallel(box)
        assert not box


def run(G: computer.Diagram, A: computer.Ty, B: computer.Ty):
    """Eq. 2.15: an X-natural family of surjections C(X × A, B) --→ C•(X,P) for each pair of types A, B."""
    del G
    return computer.Eval(A, B)


def eval_f(G: computer.Diagram):
    """Eq. 2.15: an X-natural family of surjections C(X × A, B) --→ C•(X,P) for each pair of types A, B."""
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
