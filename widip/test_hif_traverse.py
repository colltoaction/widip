import pytest
from widip.hif_traverse import cursor_step, cursor_iter

# --- Tests for Cursor Logic (Mocking Graph) ---

class MockHifNode:
    def __init__(self, incidences=None):
        self.incidences = incidences or {}

class MockHifEdge:
    def __init__(self, incidences=None):
        self.incidences = incidences or {}

# Mocking the nx_hif functions for the context of these tests
# We will use monkeypatch in the tests to redirect the imported functions in hif_traverse.py
# to our mock implementations.

def mock_hif_node_incidences(node, index, key):
    # node is our mock graph structure (dict of nodes/edges)
    # index is the node ID
    return node["nodes"].get(index, {}).get(key, [])

def mock_hif_edge_incidences(node, index, key):
    # node is our mock graph structure
    # index is the edge ID
    return node["edges"].get(index, {}).get(key, [])

@pytest.fixture
def mock_graph_functions(monkeypatch):
    monkeypatch.setattr("widip.hif_traverse.hif_node_incidences", mock_hif_node_incidences)
    monkeypatch.setattr("widip.hif_traverse.hif_edge_incidences", mock_hif_edge_incidences)

def test_cursor_step_basic(mock_graph_functions):
    graph = {
        "nodes": {
            0: {"next": [("edge1", None, None, None)]},
            1: {}
        },
        "edges": {
            "edge1": {"start": [(None, 1, None, None)]}
        }
    }

    cursor = (0, graph)
    next_cursor = cursor_step(cursor, "next")

    assert next_cursor is not None
    assert next_cursor[0] == 1
    assert next_cursor[1] is graph

def test_cursor_step_no_edge(mock_graph_functions):
    graph = {
        "nodes": {0: {}},
        "edges": {}
    }
    cursor = (0, graph)
    assert cursor_step(cursor, "next") is None

def test_cursor_step_no_neighbor(mock_graph_functions):
    graph = {
        "nodes": {
            0: {"next": [("edge1", None, None, None)]}
        },
        "edges": {
            "edge1": {} # Missing start incidence
        }
    }
    cursor = (0, graph)
    assert cursor_step(cursor, "next") is None

def test_cursor_iter(mock_graph_functions):
    # 0 -> (next) -> 1 -> (forward) -> 2 -> (forward) -> 3
    graph = {
        "nodes": {
            0: {"next": [("e0", None, None, None)]},
            1: {"forward": [("e1", None, None, None)]},
            2: {"forward": [("e2", None, None, None)]},
            3: {}
        },
        "edges": {
            "e0": {"start": [(None, 1, None, None)]},
            "e1": {"start": [(None, 2, None, None)]},
            "e2": {"start": [(None, 3, None, None)]}
        }
    }

    cursor = (0, graph)
    cursors = list(cursor_iter(cursor))

    assert len(cursors) == 3
    assert cursors[0][0] == 1
    assert cursors[1][0] == 2
    assert cursors[2][0] == 3
