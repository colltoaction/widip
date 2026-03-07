"""Section 2.5 monoidal-computer core and Run-language primitives."""

from discopy import closed, markov, monoidal, cat
from discopy.utils import factory


class ProgramOb(cat.Ob):
    """Internal object tag for the distinguished program type."""


@factory
class Ty(closed.Ty):
    def __init__(self, *inside):
        # Normalization for casts coming from DisCoPy internals:
        # `Ty(closed.Ty(...))` should denote the same wire tuple, not a nested
        # atomic object containing a whole type.
        if len(inside) == 1 and isinstance(inside[0], closed.Ty):
            inside = inside[0].inside
        closed.Ty.__init__(self, *inside)

    def tensor(self, *others):
        # Preserve distinguished subtypes when tensoring with the monoidal unit.
        if len(others) == 1:
            other = others[0]
            if len(self) == 0:
                return other
            if len(other) == 0:
                return self
        return closed.Ty.tensor(self, *others)

    # 2.5.1 b) Distinguished program type has decidable equality.
    def __eq__(self, other):
        return not isinstance(other, ProgramTy) \
            and closed.Ty.__eq__(self, other)


# factory = closed.Ty so discopy's Curry/Eval can use closed.Ty objects.
Ty.factory = closed.Ty


class ProgramTy(Ty):
    """2.5.1 b) Distinguished type P of programs with a decidable equality predicate"""
    def __init__(self):
        Ty.__init__(self, ProgramOb('P'))

    def __eq__(self, other):
        # Also accept closed.Ty(ProgramOb()) produced by factory reconstruction
        # inside discopy's Layer composability checks.
        if isinstance(other, ProgramTy):
            return True
        inside = getattr(other, 'inside', ())
        return len(inside) == 1 and isinstance(inside[0], ProgramOb)

    def __hash__(self):
        return hash(type(self))


@factory
class Diagram(markov.Diagram):
    ty_factory = Ty


class Box(markov.Box, Diagram):
   """"""


class Copy(Box, markov.Copy):
    """
    1.2, 2.5.1 a) Copying data service: ∆:A→A×A.
    """
    def __init__(self, A):
        if A:
            markov.Copy.__init__(self, A, 2)
        else:
            # ∆I = (I-id→I).
            markov.Box.__init__(self, "∆", Ty(), Ty())


class Delete(Box, markov.Discard):
    """
    1.2, 2.5.1 a) Deleting data service: A⊸I.
    """
    def __init__(self, A):
        if A:
            markov.Discard.__init__(self, A)
        else:
            # ⊸I = (I-id→I).
            markov.Box.__init__(self, "⊸", Ty(), Ty())


class Swap(Box, markov.Swap):
    """1.2"""


class Eval(Box, closed.Eval):
    """
    2.2.1.1
    2.5.1 c) Program evaluator {}:P×A→B
    """
    def __init__(self, A, B):
        self.A, self.B = A, B
        closed.Eval.__init__(self, ProgramTy() >> B)
        Box.__init__(self, "{}", ProgramTy() @ A, B)


class Partial(Box):
    """
    Sec. 2.2.2. []:P×A⊸P
    A partial evaluator is a (P×Y)-indexed program satisfying {[Γ]y}a = {Γ}(y,a).
    X=P×Y and g:P×Y×A→B
    """
    def __init__(self, X):
        self.X = X if isinstance(X, Ty) else Ty(X)
        Box.__init__(self, "[]", ProgramTy() @ self.X, ProgramTy())


class Sequential(Box):
    """
    Sec. 2.2.3. (;)_ABC:P×P⊸P
    A -{F;G}→ C = A -{F}→ B -{G}→ C
    """
    def __init__(self):
        Box.__init__(self, "(;)", ProgramTy() @ ProgramTy(), ProgramTy())


class Parallel(Box):
    """
    Sec. 2.2.3. (||)_AUBV:P×P⊸P
    A×U -{F||H}→ B×V = A -{F}→ B × U-{T}→ V
    """
    def __init__(self):
        Box.__init__(self, "(||)", ProgramTy() @ ProgramTy(), ProgramTy())


class Data(Box):
    """
    Eq. 2.6. ⌜−⌝ : A⊸P
    {}: P-→→A
    ⌜a⌝: P
    {⌜a⌝} = a
    """
    def __init__(self, A):
        self.A = A if isinstance(A, Ty) else Ty(A)
        Box.__init__(self, "⌜−⌝", ProgramTy(), self.A)


class Uncurry(monoidal.Bubble, Box):
    """
    Fig. 2.7 right-hand-side syntax: a composition-program box followed by eval.

    - `Uncurry((;), A, B, C)` stands for `((;) @ A) >> {}_{A,C}`
      with type `P×P×A⊸C`.
    - `Uncurry((||), A, U, B, V)` stands for `((||) @ A×U) >> {}_{A×U,B×V}`
      with type `P×P×A×U⊸B×V`.
    """
    def __init__(self, box, A, B):
        dom, cod = box.dom @ A, B
        # Keep uncurry as a typed layered diagram, analogous to closed.Curry.
        arg = box.bubble(dom=dom, cod=cod)
        monoidal.Bubble.__init__(self, arg, dom=dom, cod=cod, drawing_name="$\\Lambda^{-1}$")
        Box.__init__(self, f"uncurry({box.name})", dom, cod)


class Category(markov.Category):
    """2.5.1: A monoidal computer is a (symmetric, strict) monoidal category"""
    ob, ar = Ty, Diagram


def Id(x=Ty()):
    """Identity diagram over widip.computer.Ty (defaults to Ty())."""
    return Diagram.id(x)
