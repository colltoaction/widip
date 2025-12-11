from itertools import batched
from nx_yaml import nx_compose_all, nx_serialize_all
from nx_hif.hif import *

# Changed to discopy.markov
from discopy.markov import Id, Ty, Box, Hypergraph, Diagram as MarkovDiagram

# Define a custom Eval box since it's missing in Markov
class Eval(Box):
    def __init__(self, x: Ty, y: Ty):
        super().__init__("Eval", x, y)

P = Ty()

from .composing import glue_diagrams


def repl_read(stream):
    incidences = nx_compose_all(stream)
    markov_hg = hif_to_markov(incidences)
    diagrams = markov_hg.to_diagram()
    return diagrams

def incidences_to_diagram(node: HyperGraph):
    markov_hg = hif_to_markov(node)
    return markov_hg.to_diagram()

def hif_to_markov(node) -> Hypergraph:
    diagram = _incidences_to_diagram(node, 0)
    return diagram.to_hypergraph()

def markov_to_hif(markov: Hypergraph):
    """
    Converts a Markov Hypergraph back to an HIF structure (nx_hif tuple).
    Reconstructs the HIF graph by interpreting the circuit structure.

    Note: This implementation currently linearizes the structure, preserving boxes as scalar nodes.
    Complex structures like mappings and sequences represented by control boxes (e.g. `(||)`, `(;)`)
    are flattened into the stream.
    """
    G = hif_create()

    # ID counters
    next_node_id = 0
    next_edge_id = 1

    # Create root Stream (0)
    stream_id = next_node_id
    next_node_id += 2
    hif_add_node(G, stream_id, kind="stream")

    diagram = markov.to_diagram()

    # Create Document (2)
    doc_id = next_node_id
    next_node_id += 2
    hif_add_node(G, doc_id, kind="document")

    # 1. Stream Start Event (Edge 1)
    edge_stream_start = next_edge_id
    next_edge_id += 2
    hif_add_edge(G, edge_stream_start, kind="event")

    # Stream --(start)--> StreamStartEvent
    hif_add_incidence(G, edge_stream_start, stream_id, key="start")

    # 2. Document Start Event (Edge 3)
    edge_doc_start = next_edge_id
    next_edge_id += 2
    hif_add_edge(G, edge_doc_start, kind="event")

    # Connect Stream and Doc to the start event
    hif_add_incidence(G, edge_doc_start, stream_id, key="next")
    hif_add_incidence(G, edge_doc_start, stream_id, key="end")
    hif_add_incidence(G, edge_doc_start, doc_id, key="start")

    # Iterate boxes
    current_prev_node = doc_id

    for box in diagram.boxes:
        # Create a scalar node for this box
        node_id = next_node_id
        next_node_id += 2

        # Determine value and tag
        # Skip structural markers for now to provide a flattened view
        if box.name in ["(;)", "(||)"]:
            continue
        elif box.name == "⌜−⌝":
            val = box.dom[0].name if box.dom else ""
            tag = ""
        elif box.name == "G":
            if len(box.dom) > 0:
                tag = box.dom[0].name
                val = box.dom[1].name if len(box.dom) > 1 else ""
            else:
                tag = ""
                val = ""
        else:
            val = box.name
            tag = ""

        hif_add_node(G, node_id, kind="scalar", value=val, tag=tag)

        # Connect previous node -> current node
        edge_id = next_edge_id
        next_edge_id += 2

        hif_add_edge(G, edge_id, kind="event")

        # Previous node connects to this edge as NEXT and END
        hif_add_incidence(G, edge_id, current_prev_node, key="next")
        hif_add_incidence(G, edge_id, current_prev_node, key="end")

        # Current node connects to this edge as START
        hif_add_incidence(G, edge_id, node_id, key="start")

        current_prev_node = node_id

    return G


def _incidences_to_diagram(node, index) -> MarkovDiagram:
    """
    Takes an nx_yaml rooted bipartite graph
    and returns an equivalent string diagram (Markov)
    """
    node_data = hif_node(node, index)
    tag = (node_data.get("tag") or "")[1:]
    kind = node_data["kind"]

    match kind:

        case "stream":
            ob = load_stream(node, index)
        case "document":
            ob = load_document(node, index)
        case "scalar":
            ob = load_scalar(node, index, tag)
        case "sequence":
            ob = load_sequence(node, index, tag)
        case "mapping":
            ob = load_mapping(node, index, tag)
        case _:
            raise Exception(f"Kind \"{kind}\" doesn't match any.")

    return ob


def load_scalar(node, index, tag):
    v = hif_node(node, index)["value"]

    if tag == "fix" and v:
        return Box("Ω", Ty(), Ty(v)) >> Box("e", Ty(v), Ty(v))

    if tag and v:
        return Box("G", Ty(tag) @ Ty(v), Ty())
    elif tag:
        return Box("G", Ty(tag), Ty())
    elif v:
        return Box("⌜−⌝", Ty(v), Ty())
    else:
        return Box("⌜−⌝", Ty(), Ty())

def load_mapping(node, index, tag):
    ob = Id()
    i = 0
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt:
            break
        ((k_edge, _, _, _), ) = nxt
        ((_, k, _, _), ) = hif_edge_incidences(node, k_edge, key="start")
        ((v_edge, _, _, _), ) = hif_node_incidences(node, k, key="forward")
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")
        key = _incidences_to_diagram(node, k)
        value = _incidences_to_diagram(node, v)

        kv = key @ value

        if i==0:
            ob = kv
        else:
            ob = ob @ kv

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))

    par_box = Box("(||)", ob.cod, Ty())
    ob = ob >> par_box
    if tag:
         ob = Ty(tag) @ ob >> Box("G", Ty(tag) @ ob.cod, Ty())
    return ob

def load_sequence(node, index, tag):
    ob = Id()
    i = 0
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt:
            break
        ((v_edge, _, _, _), ) = nxt
        ((_, v, _, _), ) = hif_edge_incidences(node, v_edge, key="start")
        value = _incidences_to_diagram(node, v)
        if i==0:
            ob = value
        else:
            ob = ob @ value
            ob = ob >> Box("(;)", ob.cod, Ty())

        i += 1
        nxt = tuple(hif_node_incidences(node, v, key="forward"))
    if tag:
        ob = Ty(tag) @ ob >> Box("G", Ty(tag) @ ob.cod, Ty(tag))
    return ob

def load_document(node, index):
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    ob = Id()
    if nxt:
        ((root_e, _, _, _), ) = nxt
        ((_, root, _, _), ) = hif_edge_incidences(node, root_e, key="start")
        ob = _incidences_to_diagram(node, root)
    return ob

def load_stream(node, index):
    ob = Id()
    nxt = tuple(hif_node_incidences(node, index, key="next"))
    while True:
        if not nxt:
            break
        ((nxt_edge, _, _, _), ) = nxt
        starts = tuple(hif_edge_incidences(node, nxt_edge, key="start"))
        if not starts:
            break
        ((_, nxt_node, _, _), ) = starts
        doc = _incidences_to_diagram(node, nxt_node)
        if ob == Id():
            ob = doc
        else:
            try:
                ob = glue_diagrams(ob, doc)
            except:
                ob = ob >> doc

        nxt = tuple(hif_node_incidences(node, nxt_node, key="forward"))
    return ob
