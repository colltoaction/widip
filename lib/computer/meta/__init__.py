from ..common import TitiBox
from ..core import Language, Language2
from ..data import Partial

specializer_box = TitiBox("specializer", Language2, Language)
interpreter_box = TitiBox("interpreter", Language2, Language)
ackermann_box = TitiBox("ackermann", Language2, Language)

class Metaprogramming:
    @property
    def compiler(self): return Partial(interpreter_box, 1)
    @property
    def compiler_generator(self): return Partial(specializer_box, 1)
    @property
    def compiler_compiler(self): return Partial(specializer_box, 1)

meta = Metaprogramming()

__all__ = [
    "specializer_box", "interpreter_box", "ackermann_box", "meta",
    "compiler", "compiler_generator", "compiler_compiler",
    "specializer", "interpreter", "ackermann"
]

# Aliases
compiler = lambda: meta.compiler
compiler_generator = lambda: meta.compiler_generator
compiler_compiler = lambda: meta.compiler_compiler
specializer = specializer_box
interpreter = interpreter_box
ackermann = ackermann_box
