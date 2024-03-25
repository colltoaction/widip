import pathlib

import yaml
from discopy.frobenius import Ty, Diagram, Box, Id, Spider, Functor

from loader import HypergraphLoader
from composing import glue_all_diagrams


def path_diagram(path: pathlib.Path):
    # TODO during recursion some tags have relative references
    dir_d = None
    file_d = None
    if path.is_dir():
        dir_d = dir_diagram(path)
        file_path = path.with_suffix(".yaml")
        if file_path.exists():
            file_d = file_diagram(file_path)
    elif path.suffix == ".yaml":
        file_d = file_diagram(path)
        dir_path = path.with_suffix("")
        if dir_path.is_dir():
            dir_d = dir_diagram(dir_path)

    diagram = Id()
    if dir_d is not None and file_d is not None:
        # TODO introduce file_d
        # diagram = glue_diagrams(file_d, dir_d)
        diagram = dir_d
    elif dir_d is not None:
        # TODO no file
        diagram = dir_d
    elif file_d is not None:
        # TODO no dir
        diagram = file_d
    else:
        return diagram
    return diagram

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

def write_diagram(ast: Diagram) -> str:
    # TODO should be an eval'd result
    return yaml.safe_dump(tuple(x.name for x in ast.cod))


def files_ar(ar: Box) -> Diagram:
    path = pathlib.Path(ar.name)
    if path.is_file() and path.suffix == ".yaml":
        ar = file_diagram(path.open())
        Diagram.to_gif(ar, path=str(path.with_suffix('.gif')))
    elif path.is_dir():
        ar = dir_diagram(path)
        Diagram.to_gif(ar, path=str(path.with_suffix('.gif')))
    return ar

# TODO implement as monad over streams
files_f = Functor(lambda x: x, files_ar)

