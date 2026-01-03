import sys
from pathlib import Path
from yaml import YAMLError

from discopy.closed import Ty, Diagram, Box, Functor
from discopy import monoidal

from nx_yaml import nx_compose_all
from .loader import incidences_to_diagram
from .drawing import diagram_draw


def repl_read(stream):
    incidences = nx_compose_all(stream)
    return incidences_to_diagram(incidences)


def reload_diagram(path_str):
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = file_diagram(path_str)
        if hasattr(fd, "simplify"):
            fd = fd.simplify()
        diagram_draw(Path(path_str), fd)
    except YAMLError as e:
        print(e, file=sys.stderr)

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
    path = Path(file_name)
    fd = repl_read(path.open())
    
    return fd

files_f = Functor(lambda x: Ty(""), files_ar)
