"""Section 2.5 monoidal-computer core and Run-language primitives."""

from discopy import closed, markov, monoidal
from discopy.utils import factory


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


# factory = closed.Ty so discopy's Curry/Eval can use closed.Ty objects.
Ty.factory = closed.Ty


@factory
class Diagram(markov.Diagram):
    ty_factory = Ty

    def to_drawing(self):
        # Fix exponential type drawing recursion.
        return markov.Diagram.to_drawing(self, functor_factory=closed.Functor)

class Functor(markov.Functor, closed.Functor):
    """
    Preserves markov, closed, and computer boxes.
    """
    def __call__(self, other):
        if isinstance(other, Diagram):
            return other
        return Functor.__call__(self, other)


class Box(markov.Box, closed.Box, Diagram):
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
    The program evaluators are computable functions, representing typed interpreters.
    2.2.1.1
    2.5.1 c) Program evaluator {}:P×A→B
    """


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
