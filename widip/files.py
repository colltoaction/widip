import pathlib

import discopy
from discopy.frobenius import Ty, Diagram, Box, Id, Functor

from .composing import replace_id_f
from .loader import compose_all


def stream_diagram(stream):
    """a glued sequence of diagrams"""
    """consume the input stream producing one diagram at a time"""
    file_diagrams = compose_all(stream)
    file_diagrams = Functor(lambda x: x,
                            lambda b: Id(b.dom) if b.name == "!" else b)(file_diagrams)
    return file_diagrams

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
        fd = stream_diagram(path.open())
        fd = replace_id_f(path.stem)(fd)
        fd.draw(path=str(path.with_suffix(".jpg")))
        return fd
    except discopy.utils.AxiomError:
        print("diagram gluing failed -- https://github.com/colltoaction/widip/issues/2")

files_f = Functor(lambda x: Ty(""), files_ar)
