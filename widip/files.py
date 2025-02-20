import pathlib

import discopy
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
        fd = repl_read(path.read_text())
        # fd = replace_id_f(path.stem)(fd)
        fd.draw(path=str(path.with_suffix(".jpg")))
        return fd
    except discopy.utils.AxiomError:
        print("diagram gluing failed -- https://github.com/colltoaction/widip/issues/2")

files_f = Functor(lambda x: Ty(""), files_ar)
