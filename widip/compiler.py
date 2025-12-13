from discopy.closed import Ty, Box, Id, Functor, Category
from widip.box import ConstBox, RunBox
from widip.loader import P as P_loader

def compile_shell_program(diagram):
    """
    Compiles a diagram from loader.py into a diagram using explicit ShellBoxes.
    Preserves types.
    """
    return SHELL_COMPILER_FUNCTOR(diagram)

def map_box(ar):
    # Only map boxes, not other arrows like Id, Swap, etc?
    # Functor maps boxes automatically if defined.
    # ar is a Box or Structural arrow.
    if isinstance(ar, Box):
        if ar.name == "⌜−⌝":
            return ConstBox(ar.dom.name, ar.dom, ar.cod)
        if ar.name == "G":
            return RunBox(ar.dom, ar.cod)
        # TODO: Handle "g", "(||)", "(;)", etc.
    return ar

SHELL_COMPILER_FUNCTOR = Functor(
    lambda ob: ob,
    map_box,
    cod=Category(Ty, Box)
)
