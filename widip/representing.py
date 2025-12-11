from nx_hif.hif import (
    hif_create, hif_add_node, hif_add_edge, hif_add_incidence,
    hif_nodes, hif_edges, hif_edge_incidences, hif_node, hif_edge
)

from discopy.markov import Hypergraph, Ty, Box
from discopy.cat import Ob
import numbers

ATTR_BOX_NAME = "__hif_attr__"

def discopy_to_hif(diagram: Hypergraph):
    """
    Convert a discopy.markov.Hypergraph to an nx_hif structure.
    Does NOT encode diagram boundary (dom/cod) as attributes.
    Preserves all attributes via special attribute boxes.
    Infers edge IDs from incidence integer keys to satisfy nx_yaml expectations.
    """
    H = hif_create()

    # Map spider indices to HIF Node IDs
    spider_to_hif_id = {}

    # Collect attributes from ATTR_BOXES first
    spider_attrs = {i: {} for i in range(diagram.n_spiders)}

    # Identify regular boxes vs attr boxes
    regular_boxes = []

    for i, (box, (dom_wires, cod_wires)) in enumerate(zip(diagram.boxes, diagram.wires[1])):
        if box.name == ATTR_BOX_NAME and box.data:
            if dom_wires:
                spider_idx = dom_wires[0]
                k = box.data.get("key")
                v = box.data.get("value")
                if k:
                    spider_attrs[spider_idx][k] = v
        else:
            regular_boxes.append((i, box, dom_wires, cod_wires))

    # Create nodes
    for i in range(diagram.n_spiders):
        t = diagram.spider_types[i] if i < len(diagram.spider_types) else Ty()

        attrs = spider_attrs[i]
        hif_id = i # Default ID

        if "kind" not in attrs:
            kind = t.name if t.name else "scalar"
            attrs["kind"] = kind

        if attrs.get("kind") == "scalar" and "value" not in attrs:
            attrs["value"] = ""

        spider_to_hif_id[i] = hif_id
        hif_add_node(H, hif_id, **attrs)

    # Pre-calculate IDs to reserve
    box_ids = {} # original index -> edge_id
    used_ids = set(spider_to_hif_id.values())

    # Infer IDs from keys (incidences)
    for i, box, _, _ in regular_boxes:
        edge_id = None
        inc_meta = []
        if isinstance(box.data, dict) and "incidences" in box.data:
            inc_meta = box.data["incidences"]

        for m in inc_meta:
            keys_to_check = [m.get('key')]
            if 'attrs' in m:
                keys_to_check.append(m['attrs'].get('key'))

            for key in keys_to_check:
                val = None
                if isinstance(key, numbers.Integral):
                    val = int(key)
                elif isinstance(key, str) and key.isdigit():
                    val = int(key)

                if val is not None:
                    edge_id = val + 1
                    box_ids[i] = edge_id
                    used_ids.add(edge_id)
                    break
            if edge_id is not None:
                break

    # Assign remaining
    next_id = 0
    for i, box, _, _ in regular_boxes:
        if i not in box_ids:
            while next_id in used_ids:
                next_id += 1
            box_ids[i] = next_id
            used_ids.add(next_id)
            next_id += 1

    for i, box, dom_wires, cod_wires in regular_boxes:
        edge_id = box_ids[i]

        attrs = {}
        if isinstance(box.data, dict) and "attributes" in box.data:
            attrs = box.data["attributes"].copy()
            attrs.pop("_hif_id", None)
        else:
            if box.name:
                attrs["name"] = box.name
            if "kind" not in attrs:
                attrs["kind"] = "event"

        hif_add_edge(H, edge_id, **attrs)

        inc_meta = []
        if isinstance(box.data, dict) and "incidences" in box.data:
            inc_meta = box.data["incidences"]

        def get_meta(role, index):
            for m in inc_meta:
                if m.get('port_index') == index and (m.get('role') == role or (role=='cod' and m.get('role') is None)):
                    return m
            return None

        def add_inc(spider_idx, role, index):
            hif_node_id = spider_to_hif_id[spider_idx]

            meta = get_meta(role, index)
            kwargs = {}
            if meta:
                meta_attrs = meta.get('attrs', {}).copy()
                meta_attrs.pop('role', None)

                key = meta.get('key')
                if isinstance(key, str):
                    kwargs['key'] = key
                elif isinstance(key, numbers.Integral):
                    kwargs['key'] = int(key)
                elif isinstance(key, str) and key.isdigit():
                    kwargs['key'] = int(key) # Restore int if it looked like int

                kwargs.update(meta_attrs)

            hif_add_incidence(H, edge_id, hif_node_id, role=role, index=index, **kwargs)

        for j, spider_idx in enumerate(dom_wires):
            add_inc(spider_idx, "dom", j)

        for j, spider_idx in enumerate(cod_wires):
            add_inc(spider_idx, "cod", j)

    return H

def hif_to_discopy(H):
    """
    Convert an nx_hif structure to a discopy.markov.Hypergraph.
    """
    all_nodes = list(hif_nodes(H))
    all_edges = list(hif_edges(H))

    sorted_nodes = sorted(all_nodes, key=lambda x: str(x))
    node_to_idx = {n: i for i, n in enumerate(sorted_nodes)}

    # Pre-compute edge set for fast lookup
    all_edges_set = set(all_edges)

    spider_types_list = []
    attr_boxes = []

    for i, n in enumerate(sorted_nodes):
        attrs = hif_node(H, n)
        kind = attrs.get("kind") or attrs.get("type") or "scalar"

        t = Ty(str(kind))
        spider_types_list.append(t)

        attrs_to_store = attrs.copy() if attrs else {}

        for k, v in attrs_to_store.items():
            b = Box(ATTR_BOX_NAME, t, Ty(), data={"key": k, "value": v})
            attr_boxes.append((b, ((i,), ())))

    spider_types = tuple(spider_types_list)

    dom = Ty()
    cod = Ty()
    dom_wires = []
    cod_wires = []

    incidences_by_edge = {}

    I = H[2]
    if hasattr(I, "edges"):
        for u, v, key, data in I.edges(data=True, keys=True):
            edge_id = None
            node_id = None

            u_is_node = u in node_to_idx
            u_is_edge = u in all_edges_set
            v_is_node = v in node_to_idx
            v_is_edge = v in all_edges_set

            if u_is_node and v_is_edge:
                node_id = u
                edge_id = v
            elif u_is_edge and v_is_node:
                edge_id = u
                node_id = v
            elif isinstance(u, tuple) and len(u) == 2:
                if u[1] == 1: edge_id = u[0]
                elif u[1] == 0: node_id = u[0]
                if isinstance(v, tuple) and len(v) == 2:
                    if v[1] == 1: edge_id = v[0]
                    elif v[1] == 0: node_id = v[0]

            if edge_id is not None and node_id is not None:
                if edge_id not in incidences_by_edge:
                    incidences_by_edge[edge_id] = []
                incidences_by_edge[edge_id].append((node_id, key, data))

    boxes = []
    box_wires_list = []

    sorted_edges = sorted(all_edges, key=lambda x: str(x))

    for e in sorted_edges:
        attrs = hif_edge(H, e)
        attrs_copy = attrs.copy() if attrs else {}

        kind = attrs.get("kind") or attrs.get("name") or "event"
        name = str(kind)

        incs = []
        if e in incidences_by_edge:
            for node, key, data in incidences_by_edge[e]:
                incs.append((e, node, key, data))
        else:
             incs = list(hif_edge_incidences(H, e))

        def sort_key(inc):
            role = inc[3].get("role", "")
            key = str(inc[2])
            n_idx = node_to_idx.get(inc[1], -1)
            idx_attr = inc[3].get("index", -1)
            role_prio = 0 if role == 'dom' else 1 if role == 'cod' else 2
            return (role_prio, idx_attr, key, n_idx)

        sorted_incs = sorted(incs, key=sort_key)

        b_dom_wires = []
        b_cod_wires = []
        inc_metadata = []

        for i, inc in enumerate(sorted_incs):
            role = inc[3].get("role")
            node_id = inc[1]
            if node_id not in node_to_idx:
                continue

            node_idx = node_to_idx[node_id]
            meta = {
                'role': role,
                'key': inc[2],
                'attrs': inc[3],
            }

            if role == "dom":
                b_dom_wires.append(node_idx)
                meta['port_index'] = len(b_dom_wires) - 1
            elif role == "cod":
                b_cod_wires.append(node_idx)
                meta['port_index'] = len(b_cod_wires) - 1
            else:
                b_cod_wires.append(node_idx)
                meta['port_index'] = len(b_cod_wires) - 1

            inc_metadata.append(meta)

        b_dom = Ty()
        for s in b_dom_wires:
            b_dom = b_dom @ spider_types[s]

        b_cod = Ty()
        for s in b_cod_wires:
            b_cod = b_cod @ spider_types[s]

        box_data = {
            "attributes": attrs_copy,
            "incidences": inc_metadata
        }

        box = Box(name, b_dom, b_cod, data=box_data)
        boxes.append(box)
        box_wires_list.append((tuple(b_dom_wires), tuple(b_cod_wires)))

    for b, w in attr_boxes:
        boxes.append(b)
        box_wires_list.append(w)

    wires = (tuple(dom_wires), tuple(box_wires_list), tuple(cod_wires))

    return Hypergraph(dom, cod, tuple(boxes), wires, spider_types)
