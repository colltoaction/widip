import functools
import pathlib

import yaml
from discopy.frobenius import Ty, Diagram, Hypergraph as H, Box, Functor, Spider, Swap, Category, Id, Ob

from loader import HypergraphLoader
from composing import adapt_to_interface, compose_entry


def file_functor():
    return Functor(lambda x: x, file_functor_ar)

def file_functor_ar(box):
    file_diagram = compose_graph_file(box.name)
    return adapt_to_interface(file_diagram, box.to_hypergraph())

def compose_graph_file(name):
    path = pathlib.Path(name)
    f = Functor(
        ob=lambda x: replace_unnamed_wires(x, path.stem),
        ar=lambda box: Box(box.name,
                        replace_unnamed_wires(box.dom, path.stem),
                        replace_unnamed_wires(box.cod, path.stem)))
    return f(Id().tensor(*diagrams(path)))

def diagrams(path):
    if not path.exists():
        yield Id(Ty(path.stem))
    elif path.is_dir():
        file_path = path.with_suffix(".yaml")
        diagram = Id().tensor(*dir_diagrams(path))
        if file_path.exists():
            file_d = Id().tensor(*file_diagrams(file_path))
            diagram = compose_entry(file_d, diagram)
        Diagram.to_gif(diagram, path=str(path.with_suffix('.gif')))
        yield diagram
    elif path.suffix == ".yaml":
        file_d = functools.reduce(compose_entry, file_diagrams(path), Id(Ty("")))
        diagram = file_d
        dir_path = path.with_suffix("")
        if dir_path.is_dir():
            dir_d = Id().tensor(*dir_diagrams(dir_path))
            diagram = compose_entry(diagram, dir_d)
        Diagram.to_gif(diagram, path=str(path.with_suffix('.gif')))
        yield diagram
    else:
        yield Id()

def dir_diagrams(dir_path):
    for subpath in dir_path.iterdir():
        yield from diagrams(subpath)

def file_diagrams(file_path):
    yield from yaml.compose_all(open(file_path), Loader=HypergraphLoader)

def replace_unnamed_wires(ty, name):
    return Ty(*(name if x.name == "" else x.name for x in ty.inside))
