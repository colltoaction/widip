from nx_hif.hif import hif_create, hif_add_node, hif_add_edge, hif_add_incidence

from discopy.markov import Hypergraph


def to_hif(diagram: Hypergraph):
    """
    Convert a discopy.markov.Hypergraph to an nx_hif.HyperGraph.

    Spiders become Nodes.
    Boxes become Edges.
    Boundary wires are represented by "dom" and "cod" edges.
    """
    H = hif_create()

    # Add nodes for each spider
    for i in range(diagram.n_spiders):
        hif_add_node(H, i)

    # Add edge for "dom" boundary
    hif_add_edge(H, "dom")
    for i, spider_idx in enumerate(diagram.wires[0]):
        # hif_add_incidence(H, edge, node, ...)
        hif_add_incidence(H, "dom", spider_idx, role="cod", index=i)

    # Add edges for boxes
    for i, (box, (dom_wires, cod_wires)) in enumerate(zip(diagram.boxes, diagram.wires[1])):
        edge_label = f"box_{i}_{box.name}"
        hif_add_edge(H, edge_label, box=box.name)

        for j, spider_idx in enumerate(dom_wires):
            hif_add_incidence(H, edge_label, spider_idx, role="dom", index=j)

        for j, spider_idx in enumerate(cod_wires):
            hif_add_incidence(H, edge_label, spider_idx, role="cod", index=j)

    # Add edge for "cod" boundary
    hif_add_edge(H, "cod")
    for i, spider_idx in enumerate(diagram.wires[2]):
        hif_add_incidence(H, "cod", spider_idx, role="dom", index=i)

    return H
