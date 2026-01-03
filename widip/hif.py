from nx_hif.hif import hif_node_incidences, hif_edge_incidences, hif_node
from discopy.frobenius import Hypergraph, Box, Ty


def get_node_data(index, node) -> dict:
    """Returns the data associated with the node at the cursor's position."""
    return hif_node(node, index)

def to_hif(hg: Hypergraph) -> dict:
    """Serializes a DisCoPy Hypergraph to a dictionary-based HIF format"""
    nodes = {}

    spider_types = hg.spider_types
    if isinstance(spider_types, (list, tuple)):
        iterator = enumerate(spider_types)
    else:
        iterator = spider_types.items()

    for wire_id, t in iterator:
        type_name = t.name if t else ""
        nodes[str(wire_id)] = {"type": type_name}

    edges = []
    box_wires = hg.wires[1]
    for i, box in enumerate(hg.boxes):
        sources = [str(x) for x in box_wires[i][0]]
        targets = [str(x) for x in box_wires[i][1]]

        edges.append({
            "box": {
                "name": box.name,
                "dom": [x.name for x in box.dom],
                "cod": [x.name for x in box.cod],
                "data": box.data
            },
            "sources": sources,
            "targets": targets
        })

    dom_wires = [str(x) for x in hg.wires[0]]
    cod_wires = [str(x) for x in hg.wires[2]]

    return {
        "nodes": nodes,
        "edges": edges,
        "dom": dom_wires,
        "cod": cod_wires
    }

def from_hif(data: dict) -> Hypergraph:
    """ Reconstructs a DisCoPy Hypergraph from the dictionary-based HIF format"""
    sorted_node_ids = sorted(data["nodes"].keys())
    id_map = {nid: i for i, nid in enumerate(sorted_node_ids)}

    spider_types = {}
    for nid in sorted_node_ids:
        t_name = data["nodes"][nid]["type"]
        spider_types[id_map[nid]] = Ty(t_name) if t_name else Ty()

    boxes = []
    box_wires_list = []

    for edge in data["edges"]:
        sources = [id_map[s] for s in edge["sources"]]
        targets = [id_map[t] for t in edge["targets"]]

        dom_types = [spider_types[i] for i in sources]
        cod_types = [spider_types[i] for i in targets]

        dom = Ty().tensor(*dom_types)
        cod = Ty().tensor(*cod_types)

        b_spec = edge["box"]
        box = Box(b_spec["name"], dom, cod, data=b_spec.get("data"))
        boxes.append(box)
        box_wires_list.append((tuple(sources), tuple(targets)))

    dom_wires = [id_map[s] for s in data["dom"]]
    cod_wires = [id_map[s] for s in data["cod"]]

    wires = (tuple(dom_wires), tuple(box_wires_list), tuple(cod_wires))
    dom = Ty().tensor(*[spider_types[i] for i in dom_wires])
    cod = Ty().tensor(*[spider_types[i] for i in cod_wires])

    return Hypergraph(dom, cod, boxes, wires, spider_types=spider_types)


def step(index, node, key: str) -> tuple | None:
    """Advances the cursor along a specific edge key (e.g., 'next', 'forward')."""
    incidences = tuple(hif_node_incidences(node, index, key=key))
    if not incidences:
        return None
    ((edge, _, _, _), ) = incidences
    start = tuple(hif_edge_incidences(node, edge, key="start"))
    if not start:
        return None
    ((_, neighbor, _, _), ) = start

    return (neighbor, node)

def iterate(index, node):
    """Yields a sequence of (index, node) by following 'next' then 'forward' edges."""
    curr = step(index, node, "next")
    while curr:
        yield curr
        curr = step(curr[0], curr[1], "forward")
