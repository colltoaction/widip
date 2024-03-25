import pathlib
from typing import Iterator

import yaml
from discopy.frobenius import Ty, Diagram, Box, Id, Spider, Functor

from loader import HypergraphLoader
from composing import glue_diagrams


def dir_diagram(path: pathlib.Path) -> Diagram:
    """parallel composition of subfiles"""
    return Id().tensor(*(
        d
        for d in map(path_diagram, path.iterdir())
        if d))

def file_diagram(stream):
    file_diagrams = read_diagrams_st(stream)
    return glue_all_diagrams(file_diagrams)

def read_diagrams_st(stream) -> Iterator[Diagram]:
    """consume the input stream producing one diagram at a time"""
    return yaml.compose_all(stream, Loader=HypergraphLoader)

def files_ar(ar: Box) -> Diagram:
    """Uses IO to read a file or dir with the box name as path"""
    d = path_diagram(pathlib.Path(str(ar.dom)))
    if d is None:
        return Id()
    return d

def path_diagram(path: pathlib.Path) -> Diagram:
    """Uses IO to read a file or dir with the box name as path"""
    ar = None
    if path.is_file() and path.suffix == ".yaml":
        ar = file_diagram(path.open())
        Diagram.to_gif(ar, path=str(path.with_suffix('.gif')))
    elif path.is_dir():
        ar = dir_diagram(path)
        Diagram.to_gif(ar, path=str(path.with_suffix('.gif')))
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
