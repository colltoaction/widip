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
    if path.exists():
        if path.is_dir():
            diagrams = dir_diagrams(path)
            diagram = Id().tensor(*diagrams)
            diagram = adapt_to_interface(diagram, Box("", Ty(path.stem), Ty(path.stem)))
            return diagram
        else:
            diagrams = file_path_diagrams(path)
            diagram = functools.reduce(compose_entry, diagrams, Id(Ty("")))
            return diagram
    else:
        return Id(Ty(path.stem))
    # TODO the unnamed wires become the file name wires
    # return Functor(lambda x: Ty(path.stem) if x == Ty("") else x, lambda x: x)(diagram)

def dir_diagrams(dir_path):
    for subpath in dir_path.iterdir():
        if subpath.suffix == ".yaml":
            if subpath.stem == dir_path.name:
                # TODO join
                pass
                # yield from yaml.compose_all(open(subpath), Loader=HypergraphLoader)
            else:
                # yield Box(str(subpath), Ty(subpath.stem), Ty(subpath.stem))
                # print(subpath)
                yield Box(str(subpath), Ty(dir_path.stem), Ty(dir_path.stem))

def file_path_diagrams(path):
    yield from yaml.compose_all(open(path), Loader=HypergraphLoader)
