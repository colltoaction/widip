from discopy import closed
from ..common import TitiBox
from ..core import Language

class Schema(TitiBox):
    def __init__(self, name: str, dom: closed.Ty, cod: closed.Ty, *args):
        super().__init__(name.format(*args), dom, cod)

KleeneFixpoint = lambda name: Schema("fix({})", Language, Language, name)
YCombinator = lambda: TitiBox("Υ", Language, Language)
Induction = lambda b, q: Schema("⟦{}, {}⟧", Language, Language, b, q)
Recursion = lambda g, h: Schema("⟦{}, {}⟧", Language @ Language, Language, g, h)
Minimization = lambda p: Schema("μ{}", Language, Language, p)
WhileLoop = lambda t, b: Schema("while({}, {})", Language @ Language, Language, t, b)

__all__ = ["KleeneFixpoint", "YCombinator", "Induction", "Recursion", "Minimization", "WhileLoop"]
