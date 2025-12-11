import json
from discopy.markov import Hypergraph, Ty, Box
from discopy.cat import Ob
from nx_hif.hif import (
    hif_create, hif_add_node, hif_add_edge, hif_add_incidence,
    hif_nodes, hif_edges, hif_node, hif_edge
)


def discopy_to_hif(diagram: Hypergraph):
    """
    Convert a discopy.markov.Hypergraph to an nx_hif structure.
    """
    H = hif_create()
    spider_to_hif_id = {}

    # 1. Process Spiders (Nodes)
    for i in range(diagram.n_spiders):
        spider_type = diagram.spider_types[i] if i < len(diagram.spider_types) else Ty()
        attrs = _extract_spider_attrs(spider_type)

        # Restore original ID if present, otherwise use index
        hif_id = attrs.pop("_hif_id", i)

        # Ensure required attributes for valid HIF/Yaml
        if "kind" not in attrs:
            attrs["kind"] = "scalar"
            if "value" not in attrs:
                attrs["value"] = attrs.get("type", "")

        spider_to_hif_id[i] = hif_id
        hif_add_node(H, hif_id, **attrs)

    # 2. Process Boxes (Edges)
    for i, (box, (dom_wires, cod_wires)) in enumerate(zip(diagram.boxes, diagram.wires[1])):
        edge_attrs = _extract_box_attrs(box)
        edge_id = edge_attrs.pop("_hif_id", f"box_{i}")

        if "kind" not in edge_attrs:
            edge_attrs["kind"] = "event"

        hif_add_edge(H, edge_id, **edge_attrs)

        # Process Incidences
        inc_meta_list = box.data.get("incidences", []) if isinstance(box.data, dict) else []

        # Add dom incidences
        for idx, spider_idx in enumerate(dom_wires):
            meta = _find_incidence_meta(inc_meta_list, "dom", idx)
            _add_incidence(H, edge_id, spider_to_hif_id[spider_idx], "dom", idx, meta)

        # Add cod incidences
        for idx, spider_idx in enumerate(cod_wires):
            meta = _find_incidence_meta(inc_meta_list, "cod", idx)
            _add_incidence(H, edge_id, spider_to_hif_id[spider_idx], "cod", idx, meta)

    return H


def hif_to_discopy(H):
    """
    Convert an nx_hif structure to a discopy.markov.Hypergraph.
    """
    # 1. Process Nodes (Spiders)
    # Sort for deterministic order
    sorted_node_ids = sorted(list(hif_nodes(H)), key=str)
    node_to_idx = {n: i for i, n in enumerate(sorted_node_ids)}

    spider_types = []
    for n in sorted_node_ids:
        attrs = hif_node(H, n) or {}
        # Preserve ID
        attrs_with_id = attrs.copy()
        attrs_with_id["_hif_id"] = n

        try:
            # Serialize all attributes to JSON to store in Ty name
            json_str = json.dumps(attrs_with_id, sort_keys=True, default=str)
            spider_types.append(Ty(Ob(json_str)))
        except TypeError:
            name = str(attrs.get("type", ""))
            spider_types.append(Ty(name))

    # 2. Collect Incidences by Edge
    incidences_by_edge = _collect_incidences(H, node_to_idx)

    # 3. Process Edges (Boxes)
    boxes = []
    box_wires_list = []

    sorted_edge_ids = sorted(list(hif_edges(H)), key=str)

    for e in sorted_edge_ids:
        attrs = hif_edge(H, e) or {}

        # Get incidences for this edge
        incs = incidences_by_edge.get(e, [])

        # Sort incidences to determine port order
        sorted_incs = sorted(incs, key=lambda x: _incidence_sort_key(x, node_to_idx))

        dom_indices = []
        cod_indices = []
        inc_metadata = []

        for edge_id, node_id, key, data in sorted_incs:
            if node_id not in node_to_idx:
                continue

            spider_idx = node_to_idx[node_id]
            role = data.get("role")

            meta = {
                'role': role,
                'key': key,
                'attrs': data
            }

            if role == "dom":
                dom_indices.append(spider_idx)
                meta['port_index'] = len(dom_indices) - 1
            else:
                # 'cod' or None defaults to cod
                cod_indices.append(spider_idx)
                meta['port_index'] = len(cod_indices) - 1

            inc_metadata.append(meta)

        # Construct Box Types
        b_dom = Ty().tensor(*[spider_types[i] for i in dom_indices])
        b_cod = Ty().tensor(*[spider_types[i] for i in cod_indices])

        # Construct Box
        name = attrs.get("name") or attrs.get("kind") or str(e)

        box_attrs = attrs.copy()
        box_attrs["_hif_id"] = e

        box_data = {
            "attributes": box_attrs,
            "incidences": inc_metadata
        }

        boxes.append(Box(name, b_dom, b_cod, data=box_data))
        box_wires_list.append((tuple(dom_indices), tuple(cod_indices)))

    # 4. Construct Hypergraph
    # Assumes no boundary wires for the Hypergraph itself
    return Hypergraph(Ty(), Ty(), tuple(boxes), ((), tuple(box_wires_list), ()), tuple(spider_types))


# --- Helper Functions ---

def _extract_spider_attrs(t: Ty):
    attrs = {}
    if len(t.inside) == 1:
        name = t.inside[0].name
        try:
            parsed = json.loads(name)
            if isinstance(parsed, dict):
                attrs = parsed
            else:
                attrs = {"type": name}
        except (json.JSONDecodeError, TypeError):
             if name:
                attrs = {"type": name}
    elif t.name:
        attrs = {"type": t.name}
    return attrs

def _extract_box_attrs(box: Box):
    attrs = {}
    if isinstance(box.data, dict) and "attributes" in box.data:
        attrs = box.data["attributes"].copy()
    else:
        if box.name:
            attrs["name"] = box.name
        if hasattr(box, 'dom') and box.dom.name:
            attrs["dom"] = box.dom.name
        if hasattr(box, 'cod') and box.cod.name:
            attrs["cod"] = box.cod.name
    return attrs

def _find_incidence_meta(inc_meta_list, role, index):
    for m in inc_meta_list:
        if m.get('port_index') == index:
            m_role = m.get('role')
            if m_role == role:
                return m
            if role == 'cod' and m_role is None:
                return m
    return None

def _add_incidence(H, edge_id, node_id, role, index, meta):
    kwargs = {}
    if meta:
        kwargs['key'] = meta.get('key')
        kwargs['role'] = meta.get('role')
        if 'attrs' in meta:
            meta_attrs = meta['attrs'].copy()
            meta_attrs.pop('role', None)
            kwargs.update(meta_attrs)
    else:
        kwargs['role'] = role
        kwargs['index'] = index

    hif_add_incidence(H, edge_id, node_id, **kwargs)

def _collect_incidences(H, node_to_idx):
    # H[2] is the incidence graph in nx_hif structure
    incidences = {}
    I = H[2]
    all_edges_set = set(hif_edges(H))

    if hasattr(I, "edges"):
        for u, v, key, data in I.edges(data=True, keys=True):
            edge_id = None
            node_id = None

            # Determine which is edge and which is node
            if u in node_to_idx:
                node_id = u
            elif u in all_edges_set:
                edge_id = u
            elif isinstance(u, tuple) and len(u) == 2:
                if u[1] == 1: edge_id = u[0]
                elif u[1] == 0: node_id = u[0]

            if v in node_to_idx:
                node_id = v
            elif v in all_edges_set:
                edge_id = v
            elif isinstance(v, tuple) and len(v) == 2:
                if v[1] == 1: edge_id = v[0]
                elif v[1] == 0: node_id = v[0]

            if edge_id is not None and node_id is not None:
                if edge_id not in incidences:
                    incidences[edge_id] = []
                incidences[edge_id].append((edge_id, node_id, key, data))

    return incidences

def _incidence_sort_key(inc, node_to_idx):
    # inc is (edge_id, node_id, key, data)
    _, node_id, key, data = inc
    role = data.get("role", "")
    n_idx = node_to_idx.get(node_id, -1)
    idx_attr = data.get("index", -1)

    role_prio = 0 if role == 'dom' else 1 if role == 'cod' else 2

    # Sort primarily by role, then index attribute, then key, then node index
    return (role_prio, idx_attr, str(key), n_idx)
