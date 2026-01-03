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

def get_recursive_dims(d):
    """Recursively calculate effective width and height of a diagram."""
    if not hasattr(d, "boxes"):
        return 1, 1
    
    total_w = d.width
    total_h = len(d)
    
    for box in d.boxes:
        if hasattr(box, "inside"):
            iw, ih = get_recursive_dims(box.inside)
            # Add inner complexity to height (bubbles expand vertically)
            total_h += ih
            # Width is harder to estimate perfectly without layout, but adding some fraction helps
            total_w += max(0, iw - 1) * 0.5

    return total_w, total_h

def diagram_draw(path, fd):
    # Calculate figsize based on recursive diagram dimensions
    rw, rh = get_recursive_dims(fd)
    
    width = max(4, 2 + rw * 0.5)
    height = max(3, 1 + rh * 0.5)
    
    # Calculate density for textpad
    # Higher density (more boxes per unit area) needs smaller padding
    density = (len(fd) * fd.width) / (width * height)
    pad = max(0.05, min(0.3, 0.3 - density * 0.1))
    
    # Dynamic fontsize
    fsize = max(10, min(12, 120 / max(rh, rw)))

    # SVG output - vector format, scales perfectly
    fd.draw(path=str(path.with_suffix(".svg")),
            aspect="auto",
            figsize=(width, height),
            textpad=(pad, pad),
            fontsize=fsize,
            fontsize_types=int(fsize * 0.7))

files_f = Functor(lambda x: Ty(""), files_ar)
