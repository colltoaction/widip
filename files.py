import functools
import pathlib

import yaml
from discopy.frobenius import Ty, Diagram, Hypergraph as H, Box, Functor, Swap, Category, Id

from loader import HypergraphLoader
from composing import glue_diagrams, replace_box


def path_diagram(path):
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

    if dir_d is not None and file_d is not None:
        diagram = replace_box(dir_d, file_d)
        Diagram.to_gif(diagram, path=str(path.with_suffix('.gif')))
        return diagram
    elif dir_d is not None:
        Diagram.to_gif(dir_d, path=str(path.with_suffix('.gif')))
        return dir_d
    elif file_d is not None:
        Diagram.to_gif(file_d, path=str(path.with_suffix('.gif')))
        return file_d
    else:
        return Id()

def id_naming_functor(name):
    # TODO same-name box
    return Functor(
        ob=lambda x: replace_id_objects(x, name),
        ar=lambda box: Box(box.name,
                        replace_id_objects(box.dom, name),
                        replace_id_objects(box.cod, name)))

def replace_box_functor(left, right):
    """rewrites left boxes with a matching in the right"""
    return Functor(
        ob=lambda x: replace_id_objects(x, ''),
        ar=lambda box: Box(box.name,
                        replace_box(box.dom, box),
                        replace_box(box.cod, box)))

def dir_diagram(path):
    dir_diagrams = (path_diagram(subpath) for subpath in path.iterdir())
    diagram = Id().tensor(*dir_diagrams)
    # f = id_naming_functor(path.stem)
    # diagram = f(diagram)
    return diagram

def file_diagram(path):
    f = id_naming_functor(path.stem)
    file_diagrams = yaml.compose_all(open(path), Loader=HypergraphLoader)
    diagram = functools.reduce(glue_diagrams, file_diagrams, Id(Ty("")))
    diagram = f(diagram)
    return diagram

def replace_id_objects(ty, name):
    return Ty(*(name if x.name == "" else x.name for x in ty.inside))
