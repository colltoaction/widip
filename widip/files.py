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
    # Reduced figsize and margins as per feedback, while keeping increased font size
    fd.draw(path=str(path.with_suffix(".jpg")),
            # figsize was too big. Relying on default or smaller explicit size.
            # But we need to ensure text is not cut off.
            # Using margins to control spacing.
            margins=(0.2, 0.1),
            textpad=(0.4, 0.4), # Reduced padding slightly
            fontsize=16,
            fontsize_types=12)

files_f = Functor(lambda x: Ty(""), files_ar)
