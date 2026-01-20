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
    from .drawing import diagram_draw as draw_svg
    draw_svg(path, fd)

files_f = Functor(lambda x: Ty(""), files_ar)
