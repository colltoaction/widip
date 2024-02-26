import functools
import pathlib
import sys
from urllib.parse import urlparse

import yaml
from discopy.frobenius import Ty, Diagram, Hypergraph as H, Box, Functor, Spider, Swap, Category, Id, Ob
from discopy.closed import Eval
from discopy import python

from loader import HypergraphLoader
from composing import compose_entry, rewrite_functor

def swap(box):
    (l, r) = tuple(map(Ty, box.cod.inside))
    return Swap(r, l)

def eval_functor(boxes):
    ob = {}
    ar = {}
    for box in boxes:
        # TODO replacing ob clashes with other uses
        if box.name == "eval":
            (source_dom, ) = box.dom.inside
            (source_cod, ) = box.cod.inside
            eval_result = str(eval(source_dom.name) or "")
            ob[Ty(source_dom)] = Ty(eval_result)
            ob[Ty(source_cod)] = Ty(eval_result)
            # TODO replace wires
            ar[box] = Id(Ty(eval_result))
    return Functor(lambda x: ob.get(x, x), lambda x: ar.get(x, x))

def file_functor(diagram):
    ar = {}
    for box in diagram.boxes:
        # TODO replacing ob clashes with other uses
        path = pathlib.Path(box.name)
        if path.exists():
            file_diagram = compose_graph_file(path)
            ar[box] = rewrite_functor(file_diagram, box.name)(box)
    return Functor(lambda x: x, lambda x: ar.get(x, x))

def compose_graph_file(path):
    diagrams = path_diagrams(path)
    diagram = functools.reduce(compose_entry, diagrams, Id(Ty("")))
    Diagram.to_gif(diagram, path=path.with_suffix(".gif"), loop=True, timestep=100, with_labels=False)
    return diagram

def path_diagrams(path):
    if path.is_dir():
        for subpath in path.iterdir():
            if subpath.suffix == ".yaml":
                yield Box(str(subpath), Ty(""), Ty(""))
    else:
        yield from yaml.compose_all(open(path), Loader=HypergraphLoader)

native_boxes = {
    'swap': swap,
}

def compose_diagrams(diagrams):
    return functools.reduce(compose_entry, diagrams, Id(Ty("")))
