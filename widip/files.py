import pathlib

from discopy.closed import Ty, Diagram, Box, Id, Functor

from .loader import repl_read
from .representing import discopy_to_hif
from nx_yaml import nx_serialize_all


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
    hif = discopy_to_hif(fd)
    yaml_str = nx_serialize_all(hif)

    # We write to .yaml but we should be careful not to overwrite the source if it is .yaml.
    # The requirement is "change the code that creates drawings to instead output the result ... serialized to YAML"
    # Previously it was .jpg.
    # If we output to .yaml, and input is .yaml, loop is possible if watched.
    # However, widip might be used for .py files too?
    # Or purely .yaml?
    # If I output to .snapshot.yaml or similar, it's safer.

    # But strictly following "output the result... to YAML", implied outputting to a file.
    # Let's use a safe extension.

    out_path = path.with_suffix(".out.yaml")
    with open(out_path, 'w') as f:
        f.write(yaml_str)

files_f = Functor(lambda x: Ty(""), files_ar)
