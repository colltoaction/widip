from nx_yaml import nx_compose_all
import networkx as nx
import pytest

def test_read_hello_world():
    # !echo Hello world!
    with open("examples/hello-world.yaml") as f:
        h = nx_compose_all(f)

    # nx_compose_all returns a HyperGraph, which is a tuple of graphs
    assert isinstance(h, tuple)
    assert len(h) >= 1

    # The first element is usually the main structure graph
    graph = h[0]
    assert isinstance(graph, nx.MultiDiGraph)
    assert len(graph.nodes) > 0

    # Check for tag "echo"
    tags = [d.get("tag") for _, d in graph.nodes(data=True) if "tag" in d]
    assert any("echo" in t for t in tags)

def test_read_shell():
    # examples/shell.yaml
    with open("examples/shell.yaml") as f:
        h = nx_compose_all(f)

    assert isinstance(h, tuple)
    graph = h[0]
    assert isinstance(graph, nx.MultiDiGraph)
    assert len(graph.nodes) > 0

    tags = [d.get("tag") for _, d in graph.nodes(data=True) if "tag" in d]
    tag_names = {"!cat", "!wc", "!grep", "!tail"}

    matches = 0
    for t in tags:
        if any(target.strip("!") in t for target in tag_names):
            matches += 1
    assert matches > 0
