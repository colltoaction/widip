import sys
from pathlib import Path
from yaml import YAMLError

from discopy.closed import Ty, Diagram, Box, Functor

from nx_yaml import nx_compose_all
from .loader import incidences_to_diagram


def repl_read(stream):
    incidences = nx_compose_all(stream)
    return incidences_to_diagram(incidences)


def reload_diagram(path_str):
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = file_diagram(path_str).simplify()
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

def diagram_draw(path, fd):
    # Calculate figsize based on diagram dimensions
    # Tighter layout: reduced base dimensions and scaling factors
    width = max(3, 1 + fd.width * 0.5)
    height = max(2, 1 + len(fd) * 0.4)
    
    # SVG output - vector format, scales perfectly
    fd.draw(path=str(path.with_suffix(".svg")),
            aspect="auto",
            figsize=(width, height),
            textpad=(0.1, 0.05),
            fontsize=11,
            fontsize_types=8)

files_f = Functor(lambda x: Ty(""), files_ar)
