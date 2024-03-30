import pathlib
from typing import Iterator

import yaml
from discopy.frobenius import Ty, Diagram, Box, Id, Spider, Functor

from loader import HypergraphLoader
from composing import adapt_to_interface, glue_diagrams, replace_id_f


def dir_diagram(path: pathlib.Path) -> Diagram:
    """a tensor of subfiles diagrams"""
    return Id().tensor(*(d for d in map(path_diagram, path.iterdir()) if d))
    # return glue_all_diagrams((
    #     Id("io"),
    #     Id().tensor(*(d for d in map(path_diagram, path.iterdir()) if d)),
    #     Id("io")))

def file_diagram(stream):
    """a glued sequence of diagrams"""
    file_diagrams = read_diagrams_st(stream)
    return glue_all_diagrams(file_diagrams)

def read_diagrams_st(stream) -> Iterator[Diagram]:
    """consume the input stream producing one diagram at a time"""
    return yaml.compose_all(stream, Loader=HypergraphLoader)

def files_ar(ar: Box) -> Diagram:
    """Uses IO to read a file or dir with the box name as path"""
    if not ar.name.startswith("file://"):
        return ar

    path = pathlib.Path(ar.name.lstrip("file://"))
    d = path_diagram(path)
    if d is None:
        return ar
    # TODO the contract is io->io.
    # TODO this can be done outside
    # d = adapt_to_interface(d, Id(""))
    return d

def path_diagram(path: pathlib.Path) -> Diagram:
    """Uses IO to read a file or dir with the box name as path"""
    # TODO paths dom=cod=io
    # TODO set up file change notifications
    ar = None
    if path.is_file() and path.suffix == ".yaml":
        ar = file_diagram(path.open())
        Diagram.to_gif(ar, path=str(path.with_suffix('.gif')))
    elif path.is_dir():
        ar = dir_diagram(path)
        Diagram.to_gif(ar, path=str(path.with_suffix('.gif')))
    # TODO rename file name to io
    if ar is not None:
        ar = replace_id_f(path.stem)(ar)
    return ar

def glue_all_diagrams(file_diagrams) -> Diagram:
    i = 0
    diagram = None
    for d in file_diagrams:
        if i == 0:
            diagram = d
        else:
            diagram = glue_diagrams(diagram, d)
        i += 1
    if i == 0:
        return Id()
    return diagram

files_f = Functor(lambda x: Ty(""), files_ar)
