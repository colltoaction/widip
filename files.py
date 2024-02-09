import functools
import pathlib
import sys

import yaml
from discopy.frobenius import Ty, Diagram, Hypergraph as H, Box, Functor, Spider, Swap

from loader import HypergraphLoader, compose_entry

def swap(box):
    (l, r) = tuple(map(Ty, box.cod.inside))
    return Swap(r, l)

boxes = {
    'swap': swap
}
def compose_graphs(graphs):
    graph = functools.reduce(
        lambda k, v: k >> v,
        graphs)
    f = Functor(
        ob=lambda x: x,
        ar={box: boxes[box.name](box) if box.name in boxes else box for box in graph.boxes})
    graph = f(graph.to_diagram())
    return graph

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
