from nx_hif.hif import (
    hif_create, hif_add_node, hif_add_edge, hif_add_incidence,
    hif_nodes, hif_edges, hif_edge_incidences, hif_edge
)

from discopy.markov import Hypergraph, Ty, Box


def discopy_to_hif(diagram: Hypergraph):
    """
    Convert a discopy.markov.Hypergraph to an nx_hif.HyperGraph.
    """
    H = hif_create()

    # Map spider indices to node IDs
    # We use integer IDs matching spider indices
    for i in range(diagram.n_spiders):
        # We store the type if available
        # diagram.spider_types is a map {spider_idx: type} or list?
        # In markov.Hypergraph, spider_types is a tuple of types corresponding to spiders 0..n-1
        # if explicitly provided or inferred.
        # But wait, diagram.spider_types might be None or inferred.
        # Let's check accessing it.
        # diagram.spider_types returns the map/tuple.
        t = diagram.spider_types[i] if i < len(diagram.spider_types) else Ty()
        # We can store type name as attribute?
        hif_add_node(H, i, type=t.name)

    # Add edge for "dom" boundary
    hif_add_edge(H, "dom")
    for i, spider_idx in enumerate(diagram.wires[0]):
        hif_add_incidence(H, "dom", spider_idx, role="cod", index=i)

    # Add edges for boxes
    # diagram.wires[1] is tuple of box wires.
    # box wires is (dom_wires, cod_wires).
    for i, (box, (dom_wires, cod_wires)) in enumerate(zip(diagram.boxes, diagram.wires[1])):
        edge_label = f"box_{i}_{box.name}"
        # Store box attributes
        hif_add_edge(H, edge_label, name=box.name, dom=box.dom.name, cod=box.cod.name)

        for j, spider_idx in enumerate(dom_wires):
            hif_add_incidence(H, edge_label, spider_idx, role="dom", index=j)

        for j, spider_idx in enumerate(cod_wires):
            hif_add_incidence(H, edge_label, spider_idx, role="cod", index=j)

    # Add edge for "cod" boundary
    hif_add_edge(H, "cod")
    for i, spider_idx in enumerate(diagram.wires[2]):
        hif_add_incidence(H, "cod", spider_idx, role="dom", index=i)

    return H

def hif_to_discopy(H):
    """
    Convert an nx_hif.HyperGraph back to discopy.markov.Hypergraph.
    """
    # 1. Spiders
    # We assume nodes are integers 0..N-1
    # But nx_hif might return them unordered or mixed.
    # We need to reconstruct the mapping.
    # encode used 0..n_spiders-1.

    # Filter nodes (exclude edges if mixed, though hif_nodes usually implies nodes)
    # But as seen in tests, adding incidence adds edge to nodes in nx_hif implementation?
    # We can filter by checking if it's an integer? Or checking attributes?
    # Or simpler: all nodes that are NOT "dom", "cod" or "box_..."

    # Let's collect all nodes that look like spiders (ints)
    spider_nodes = []
    node_to_idx = {}

    # Helper to get attributes if possible, hif_nodes returns list of keys.
    # hif_node(H, n) gets attrs.

    all_nodes = list(hif_nodes(H))

    # Identify spiders. In encode we used ints.
    spiders = [n for n in all_nodes if isinstance(n, int)]
    spiders.sort()

    # Construct spider_types
    # We need to retrieve type info.
    # We assumed we stored it in 'type'.
    # But wait, hif_add_node(H, i, type=...) might not store it if H doesn't support attrs or I used it wrong.
    # But assuming it works:
    from nx_hif.hif import hif_node

    spider_types_list = []
    for s in spiders:
        attrs = hif_node(H, s)
        t_name = attrs.get("type", "")
        spider_types_list.append(Ty(t_name) if t_name else Ty())

    spider_types = tuple(spider_types_list)

    # 2. Wires
    # dom wires: incidences of "dom" edge
    dom_incs = sorted(list(hif_edge_incidences(H, "dom")), key=lambda x: x[3].get("index", 0))
    # inc structure: (edge, node, key, attrs)
    dom_wires = tuple(inc[1] for inc in dom_incs)

    # cod wires
    cod_incs = sorted(list(hif_edge_incidences(H, "cod")), key=lambda x: x[3].get("index", 0))
    cod_wires = tuple(inc[1] for inc in cod_incs)

    # 3. Boxes
    # Identify box edges. They start with "box_"
    all_edges = list(hif_edges(H))
    box_edges = [e for e in all_edges if str(e).startswith("box_")]

    # Sort by index in label "box_{i}_{name}" to preserve order
    def extract_index(label):
        parts = str(label).split("_")
        return int(parts[1])

    box_edges.sort(key=extract_index)

    boxes = []
    box_wires_list = []

    for e in box_edges:
        attrs = hif_edge(H, e)
        name = attrs.get("name", "f")
        dom_name = attrs.get("dom", "")
        cod_name = attrs.get("cod", "")

        # dom = Ty(dom_name) # This assumes atomic types name works like this.
        # But Ty("a", "b") name is "a @ b"? No.
        # Ty("a", "b").name -> "a @ b"?
        # Let's assume simple types or reconstruct from spiders.
        # Reconstructing from spiders is safer if we trust spider_types.

        # Get incidences
        incs = list(hif_edge_incidences(H, e))

        # dom wires: role="dom"
        b_dom_incs = sorted([inc for inc in incs if inc[3].get("role") == "dom"], key=lambda x: x[3].get("index", 0))
        b_dom_wires = tuple(inc[1] for inc in b_dom_incs)

        # cod wires: role="cod"
        b_cod_incs = sorted([inc for inc in incs if inc[3].get("role") == "cod"], key=lambda x: x[3].get("index", 0))
        b_cod_wires = tuple(inc[1] for inc in b_cod_incs)

        # Infer type from spiders?
        # Or parse Ty(name)?
        # Discopy boxes need Types.
        # If we use the types stored in attrs:
        # dom = Ty(dom_name) implies Ty("a @ b") which creates one object "a @ b".
        # If the original was Ty("a", "b"), name is "a @ b".
        # We should probably use the spider types to determine box types?
        # But for generic Box, explicit types are needed.
        # Let's try to parse the name if it's "a @ b".
        # Or better, just use the types of the wires connected.
        # spider_types map: spider_idx -> Ty
        # box_dom = sum(spider_types[s] for s in b_dom_wires, Ty())

        b_dom = Ty()
        for s in b_dom_wires:
             # Find index of s in spiders list
             idx = spiders.index(s)
             b_dom = b_dom @ spider_types[idx]

        b_cod = Ty()
        for s in b_cod_wires:
             idx = spiders.index(s)
             b_cod = b_cod @ spider_types[idx]

        box = Box(name, b_dom, b_cod)
        boxes.append(box)
        box_wires_list.append((b_dom_wires, b_cod_wires))

    wires = (dom_wires, tuple(box_wires_list), cod_wires)

    # dom and cod of the whole diagram
    dom = Ty()
    for s in dom_wires:
         idx = spiders.index(s)
         dom = dom @ spider_types[idx]

    cod = Ty()
    for s in cod_wires:
         idx = spiders.index(s)
         cod = cod @ spider_types[idx]

    return Hypergraph(dom, cod, tuple(boxes), wires, spider_types)
