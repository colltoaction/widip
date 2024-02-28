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
    diagram = Id(Ty(path.stem))
    if not path.exists():
        return diagram
    if path.is_dir():
        diagrams = dir_diagrams(path)
        diagram = Id().tensor(*diagrams)
        diagram = adapt_to_interface(diagram, Box("", Ty(path.stem), Ty(path.stem)))
        diagram = file_functor()(diagram)
    else:
        f = Functor(
            ob=lambda x: replace_unnamed_wires(x, path.parent.name),
            ar=lambda box: Box(box.name,
                            replace_unnamed_wires(box.dom, path.parent.name),
                            replace_unnamed_wires(box.cod, path.parent.name)))
        diagrams = yaml.compose_all(open(path), Loader=HypergraphLoader)
        diagram = functools.reduce(compose_entry, diagrams, Id(Ty("")))
        diagram = f(diagram)
    Diagram.to_gif(diagram, path=str(path.with_suffix('.gif')))
    return diagram

def dir_diagrams(dir_path):
    for subpath in dir_path.iterdir():
        if subpath.suffix == ".yaml":
            yield Box(str(subpath), Ty(dir_path.name), Ty(dir_path.name))

def replace_unnamed_wires(ty, name):
    return Ty(*(name if x.name == "" else x.name for x in ty.inside))
