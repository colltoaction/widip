import networkx as nx
from discopy.markov import Diagram, Box, Ty, Hypergraph
from nx_hif.hif import hif_create, hif_new_node, hif_new_edge, hif_add_incidence

# HIF conventions
BOUNDARY_KIND = "_boundary"
NODE_GRAPH_IDX = 0
EDGE_GRAPH_IDX = 1

def hif_to_discopy(hg) -> Diagram:
    nodes, edges, incidences = hg

    # Identify _boundary node
    boundary = None
    for n, data in nodes.nodes(data=True):
        if data.get("kind") == BOUNDARY_KIND:
            boundary = n
            break

    # Map edges to spider indices (0..N-1)
    edge_ids = sorted(list(edges.nodes()))
    edge_to_spider = {eid: i for i, eid in enumerate(edge_ids)}

    spider_types = {}
    for eid, s_idx in edge_to_spider.items():
        # Default type for now
        spider_types[s_idx] = Ty("•")

    def get_ports(nid, role_filter):
        ports = []
        # Incidence node for nid is (nid, NODE_GRAPH_IDX)
        u_key = (nid, NODE_GRAPH_IDX)

        if u_key not in incidences:
            return []

        for _, v, k, d in incidences.edges(nbunch=u_key, keys=True, data=True):
            # v is (eid, EDGE_GRAPH_IDX)
            eid, graph_idx = v
            if graph_idx != EDGE_GRAPH_IDX: continue # Should not happen

            if eid not in edge_to_spider: continue

            role = d.get("role")
            if role == role_filter:
                index = d.get("index", 0)
                ports.append((index, edge_to_spider[eid]))
        ports.sort()
        return [p[1] for p in ports]

    # Global dom/cod
    dom_wires = []
    cod_wires = []
    if boundary is not None:
        dom_wires = get_ports(boundary, "dom")
        cod_wires = get_ports(boundary, "cod")

    # Boxes
    boxes = []
    box_wires = []

    # Filter nodes (exclude boundary)
    node_ids = [n for n in nodes.nodes() if (boundary is None or n != boundary)]
    # Sort for deterministic order
    node_ids.sort(key=lambda x: str(x))

    for nid in node_ids:
        data = nodes.nodes[nid]
        kind = data.get("kind", "box")

        ins = get_ports(nid, "dom")
        outs = get_ports(nid, "cod")

        dom_ty = Ty()
        for _ in ins: dom_ty = dom_ty @ Ty("•")

        cod_ty = Ty()
        for _ in outs: cod_ty = cod_ty @ Ty("•")

        box_data = data.copy()
        if "kind" in box_data: del box_data["kind"]

        box = Box(kind, dom_ty, cod_ty, data=box_data)
        boxes.append(box)
        box_wires.append((tuple(ins), tuple(outs)))

    dom_ty = Ty()
    for _ in dom_wires: dom_ty = dom_ty @ Ty("•")

    cod_ty = Ty()
    for _ in cod_wires: cod_ty = cod_ty @ Ty("•")

    dhg = Hypergraph(dom_ty, cod_ty, tuple(boxes),
                     (tuple(dom_wires), tuple(box_wires), tuple(cod_wires)),
                     spider_types)

    return dhg.to_diagram()

def discopy_to_hif(diagram: Diagram):
    hg = diagram.to_hypergraph()

    hif_graph = hif_create()

    # Create spiders (edges)
    spider_to_eid = {}
    for i in range(hg.n_spiders):
        eid = hif_new_edge(hif_graph, kind="spider")
        spider_to_eid[i] = eid

    # Create boundary
    boundary_id = hif_new_node(hif_graph, kind=BOUNDARY_KIND)

    # Connect boundary
    dom_wires = hg.wires[0]
    for i, spider_idx in enumerate(dom_wires):
        eid = spider_to_eid[spider_idx]
        hif_add_incidence(hif_graph, eid, boundary_id, role="dom", index=i, key=None)

    cod_wires = hg.wires[2]
    for i, spider_idx in enumerate(cod_wires):
        eid = spider_to_eid[spider_idx]
        hif_add_incidence(hif_graph, eid, boundary_id, role="cod", index=i, key=None)

    # Create boxes
    box_wires = hg.wires[1]
    for i, box in enumerate(hg.boxes):
        data = box.data.copy() if box.data else {}
        data["kind"] = box.name
        nid = hif_new_node(hif_graph, **data)

        ins, outs = box_wires[i]
        for idx, spider_idx in enumerate(ins):
            eid = spider_to_eid[spider_idx]
            hif_add_incidence(hif_graph, eid, nid, role="dom", index=idx, key=None)

        for idx, spider_idx in enumerate(outs):
            eid = spider_to_eid[spider_idx]
            hif_add_incidence(hif_graph, eid, nid, role="cod", index=idx, key=None)

    return hif_graph
