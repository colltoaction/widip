from ..common import TitiBox
from ..core import Language
from discopy import closed

TRUE = lambda: TitiBox("⊤", closed.Ty(), Language, draw_as_spider=True)()
FALSE = lambda: TitiBox("⊥", closed.Ty(), Language, draw_as_spider=True)()
IFTE = lambda: TitiBox("ifte", Language @ Language @ Language, Language)
ProgramEq = lambda: TitiBox("=?", Language @ Language, Language)

ZERO = lambda: TitiBox("0", closed.Ty(), Language)()
SUCC = TitiBox("s", Language, Language)
PRED = TitiBox("r", Language, Language)
ISZERO = TitiBox("0?", Language, Language)

class NaturalNumber(TitiBox):
    def __init__(self, n: int):
        super().__init__(str(n), closed.Ty(), Language, data=n)

__all__ = ["TRUE", "FALSE", "IFTE", "ProgramEq", "ZERO", "SUCC", "PRED", "ISZERO", "NaturalNumber"]
