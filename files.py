import functools
import pathlib
import sys

import yaml
from discopy.frobenius import Ty, Diagram, Hypergraph as H

from loader import HypergraphLoader, compose_entry


def compose_graphs(graphs):
    graph = functools.reduce(
        compose_entry,
        # lambda k, v: k << v,
        graphs)
    # graph.draw()
    return graph.to_diagram()

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
