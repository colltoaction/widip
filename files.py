import functools
import pathlib
import sys

import yaml
from discopy.frobenius import Ty, Diagram, Hypergraph as H, Box, Functor, Spider, Swap, Category, Id, Ob
from discopy.closed import Eval
from discopy import python

from loader import HypergraphLoader, compose_entry

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

native_boxes = {
    'swap': swap,
}
def compose_graphs(graphs):
    graph = functools.reduce(
        compose_entry,
        # lambda k, v: k >> v,
        graphs)
    # f = Functor(
    #     ob=lambda x: x,
    #     ar={box: native_boxes[box.name](box) if box.name in native_boxes else box for box in graph.boxes})
    # graph = f(graph.to_diagram())
    # f2 = eval_functor(graph.boxes)
    # # graph.draw()
    # graph = f2(graph)
    return graph.to_diagram()

# TODO expose this in the DSL to start bootstrapping.
# e.g detect !tag when tag dir and/or tag.yaml are present.
def compose_graph_file(path: pathlib.Path):
    if path.is_dir():
        # TODO
        G = compose_dir(path)
    else:
        G = (
            # H.id(),
            *yaml.compose_all(open(path), Loader=HypergraphLoader),
            # H.id(),
        )
    diagram = compose_graphs(G)
    # try:
    #     diagram = diagram.normal_form()
    # except Exception as ex:
    #     diagram = ex.last_step
    # TODO temporary path
    Diagram.to_gif(diagram, path=path.with_suffix(".gif"), loop=True, timestep=100, with_labels=False)
    return diagram

def compose_all_graphs():
    paths = iter(sys.argv[1:])
    for f in paths:
        compose_graph_file(pathlib.Path(f))

def compose_dir(path):
    diagram = H.id()
    for subpath in path.iterdir():
        if subpath.suffix == ".yaml":
            diagram @= H.id(Ty(subpath.stem))
    yield diagram
