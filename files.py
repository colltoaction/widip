import functools
import pathlib

import yaml
from discopy.frobenius import Ty, Diagram, Hypergraph as H, Box, Functor, Swap, Category, Id

from loader import HypergraphLoader
from composing import glue_diagrams


def path_diagram(path):
    # TODO during recursion some tags have relative references
    dir_d = None
    file_d = None
    # f = box_expansion_functor()
    if path.is_dir():
        dir_d = dir_diagram(path)
        file_path = path.with_suffix(".yaml")
        if file_path.exists():
            file_d = file_diagram(file_path)
            # file_d = f(file_d)
    elif path.suffix == ".yaml":
        file_d = file_diagram(path)
        dir_path = path.with_suffix("")
        if dir_path.is_dir():
            dir_d = dir_diagram(dir_path)

    if dir_d is not None and file_d is not None:
        # dir_d = f(dir_d)
        diagram = glue_diagrams(file_d, dir_d)
        Diagram.to_gif(diagram, path=str(path.with_suffix('.gif')))
        return diagram
    elif dir_d is not None:
        Diagram.to_gif(dir_d, path=str(path.with_suffix('.gif')))
        return dir_d
    elif file_d is not None:
        # file_d = f(file_d)
        Diagram.to_gif(file_d, path=str(path.with_suffix('.gif')))
        return file_d
    else:
        return Id()

def id_naming_functor(name):
    # TODO same-name box
    return Functor(
        ob=lambda x: replace_id_objects(x, name),
        ar=lambda box: Id(box.name)
                        if box.name == box.dom.name == box.cod.name
                        else Box(box.name,
                        replace_id_objects(box.dom, name),
                        replace_id_objects(box.cod, name)))

def dir_diagram(path):
    dir_diagrams = (path_diagram(subpath) for subpath in path.iterdir())
    diagram = Id().tensor(*dir_diagrams)
    # f = id_naming_functor(path.stem)
    # diagram = f(diagram)
    return diagram

def file_diagram(path):
    f = id_naming_functor(path.stem)
    file_diagrams = yaml.compose_all(open(path), Loader=HypergraphLoader)
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

def replace_id_objects(ty, name):
    return Ty(*(name if x.name == "" else x.name for x in ty.inside))
