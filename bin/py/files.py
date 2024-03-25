import pathlib

import yaml
from discopy.frobenius import Ty, Diagram, Box, Id, Spider, Functor

from loader import HypergraphLoader
from composing import glue_all_diagrams


def dir_diagram(path: pathlib.Path) -> Diagram:
    """walks a directory to create a diagram"""
    if path.is_file() and path.suffix == ".yaml":
        return Box(path.stem, Ty(""), Ty(""))
    elif path.is_dir():
        mid = Id().tensor(*(
            d
            # d.name
            for d in map(dir_diagram, path.iterdir())
            if d != Id()))
        if mid == Id():
            return Id()
        return Box(path.stem, Ty(""), mid.dom,) \
            >> mid \
            >> Spider(len(mid.cod), 1, Ty(""))
    else:
        return Id()

def file_diagram(stream):
    file_diagrams = read_diagrams_st(stream)
    return glue_all_diagrams(file_diagrams)

def read_diagrams_st(stream) -> Diagram:
    return yaml.compose_all(stream, Loader=HypergraphLoader)

def files_ar(ar: Box) -> Diagram:
    """Uses IO to read a file or dir with the box name as path"""
    path = pathlib.Path(str(ar.dom))
    if path.is_file() and path.suffix == ".yaml":
        ar = file_diagram(path.open())
        Diagram.to_gif(ar, path=str(path.with_suffix('.gif')))
    elif path.is_dir():
        ar = dir_diagram(path)
        Diagram.to_gif(ar, path=str(path.with_suffix('.gif')))
    return ar

