import pathlib

from discopy.utils import AxiomError
from discopy.frobenius import Ty, Diagram, Box, Id, Functor

from .loader import repl_read


def files_ar(ar: Box) -> Diagram:
    """Uses IO to read a file or dir with the box name as path"""
    if not ar.name.startswith("file://"):
        return ar

    try:
        return file_diagram(ar.name.lstrip("file://"))
    except IsADirectoryError:
        print("is a dir")
        return ar

def file_diagram(file_name) -> Diagram:
    try:
        path = pathlib.Path(file_name)
        fd = repl_read(path.open())
        # TODO TypeError: Expected frobenius.Diagram, got monoidal.Diagram instead
        # fd = replace_id_f(path.stem)(fd)
        fd.draw(path=str(path.with_suffix(".jpg")),
                textpad=(0.3, 0.1),
                fontsize=12,
                fontsize_types=8)
        return fd
    except AxiomError:
        print("diagram gluing failed -- https://github.com/colltoaction/widip/issues/2")

files_f = Functor(lambda x: Ty(""), files_ar)
