from discopy.symmetric import Hypergraph, Box, Ty


def to_hif(hg: Hypergraph) -> dict:
    """Serializes a DisCoPy Hypergraph to a dictionary-based HIF format"""
    nodes = {}
    for i, t in enumerate(hg.spider_types):
        type_name = t[0].name if t else ""
        nodes[str(i)] = {"type": type_name}

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
    # Map HIF node IDs to contiguous integers 0..N-1
    # Sorting ensures deterministic mapping
    sorted_node_ids = sorted(data["nodes"].keys())
    id_map = {nid: i for i, nid in enumerate(sorted_node_ids)}

    spider_types = []
    for nid in sorted_node_ids:
        t_name = data["nodes"][nid]["type"]
        spider_types.append(Ty(t_name) if t_name else Ty())

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

    return Hypergraph(dom, cod, boxes, wires, spider_types=tuple(spider_types))
