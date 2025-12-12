import pathlib

from discopy.closed import Ty, Diagram, Box, Id, Functor

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
    path = pathlib.Path(file_name)
    fd = repl_read(path.open())
    # TODO TypeError: Expected closed.Diagram, got monoidal.Diagram instead
    # fd = replace_id_f(path.stem)(fd)
    return fd

def diagram_draw(path, fd):
    # Drastic increase in figsize and margins
    fd.draw(path=str(path.with_suffix(".jpg")),
            figsize=(12, 8), # Increased figure size
            textpad=(0.7, 0.7),
            margins=(1.0, 0.5),
            fontsize=16,
            fontsize_types=12)

files_f = Functor(lambda x: Ty(""), files_ar)
