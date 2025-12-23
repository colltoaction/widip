import sys
from pathlib import Path
from yaml import YAMLError

from discopy.closed import Ty, Diagram, Box, Functor

from .loader import repl_read


def reload_diagram(path_str):
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = file_diagram(path_str)
        diagram_draw(Path(path_str), fd)
        diagram_draw(Path(path_str+".2"), fd)
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
    fd.draw(path=str(path.with_suffix(".jpg")),
            textpad=(0.3, 0.1),
            fontsize=12,
            fontsize_types=8)

files_f = Functor(lambda x: Ty(""), files_ar)
