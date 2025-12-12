from nx_hif.hif import (
    hif_create, hif_add_node, hif_add_edge, hif_add_incidence,
    hif_nodes, hif_edges, hif_edge_incidences, hif_node, hif_edge
)

from discopy.markov import Hypergraph, Ty, Box
from discopy.cat import Ob
import json

def discopy_to_hif(diagram: Hypergraph):
    """
    Convert a discopy.markov.Hypergraph to an nx_hif structure.
    Preserves original HIF IDs if present in attributes.
    """
    H = hif_create()

    # Map spider indices to HIF Node IDs
    spider_to_hif_id = {}

    for i in range(diagram.n_spiders):
        t = diagram.spider_types[i] if i < len(diagram.spider_types) else Ty()

        attrs = {}
        hif_id = i # Default ID

        # Try to parse attributes from Ty name (JSON)
        if len(t.inside) == 1:
            name = t.inside[0].name
            try:
                attrs = json.loads(name)
                if not isinstance(attrs, dict):
                    attrs = {"type": name}
            except (json.JSONDecodeError, TypeError):
                if name:
                    attrs = {"type": name}
        elif t.name:
             attrs = {"type": t.name}

        # Restore original ID
        if "_hif_id" in attrs:
            hif_id = attrs.pop("_hif_id")

        # Ensure 'kind' attribute for nx_yaml
        if "kind" not in attrs:
            attrs["kind"] = "scalar"
            if "value" not in attrs:
                attrs["value"] = attrs.get("type", "")

        spider_to_hif_id[i] = hif_id
        hif_add_node(H, hif_id, **attrs)

    # Helper to add incidences
    # We need to track keys per edge to avoid overwriting
    next_key = {}

    def add_inc(edge_id, spider_idx, role, index, meta_override=None):
        hif_node_id = spider_to_hif_id[spider_idx]

        # Determine key
        k = None
        if meta_override and 'key' in meta_override:
            k = meta_override['key']
        else:
            if edge_id not in next_key:
                next_key[edge_id] = 0
            k = next_key[edge_id]
            next_key[edge_id] += 1

        if meta_override:
            meta_attrs = meta_override.get('attrs', {}).copy()
            meta_attrs.pop('role', None)
            hif_add_incidence(H, edge_id, hif_node_id, key=k, role=meta_override.get('role'), **meta_attrs)
        else:
            hif_add_incidence(H, edge_id, hif_node_id, key=k, role=role, index=index)

    # Add edges for boxes
    for i, (box, (dom_wires, cod_wires)) in enumerate(zip(diagram.boxes, diagram.wires[1])):
        edge_id = f"box_{i}"

        attrs = {}
        if isinstance(box.data, dict) and "attributes" in box.data:
            attrs = box.data["attributes"].copy()
            if "_hif_id" in attrs:
                edge_id = attrs.pop("_hif_id")
        else:
            if box.name:
                attrs["name"] = box.name
            if box.dom.name:
                attrs["dom"] = box.dom.name
            if box.cod.name:
                attrs["cod"] = box.cod.name

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

        for j, spider_idx in enumerate(dom_wires):
            add_inc(edge_id, spider_idx, "dom", j, get_meta("dom", j))

        for j, spider_idx in enumerate(cod_wires):
            add_inc(edge_id, spider_idx, "cod", j, get_meta("cod", j))

    # Add global boundary edge if there are open wires
    if len(diagram.wires[0]) > 0 or len(diagram.wires[2]) > 0:
        boundary_id = "_boundary"
        attrs = {"kind": "boundary"}
        if diagram.dom.name:
            attrs["dom"] = diagram.dom.name
        if diagram.cod.name:
            attrs["cod"] = diagram.cod.name

        hif_add_edge(H, boundary_id, **attrs)

        for j, spider_idx in enumerate(diagram.wires[0]):
            add_inc(boundary_id, spider_idx, "dom", j)

        for j, spider_idx in enumerate(diagram.wires[2]):
            add_inc(boundary_id, spider_idx, "cod", j)

    return H

def hif_to_discopy(H):
    """
    Convert an nx_hif structure to a discopy.markov.Hypergraph.
    """
    all_nodes = list(hif_nodes(H))
    all_edges = list(hif_edges(H))

    sorted_nodes = sorted(all_nodes, key=lambda x: str(x))
    node_to_idx = {n: i for i, n in enumerate(sorted_nodes)}

    spider_types_list = []

    for i, n in enumerate(sorted_nodes):
        attrs = hif_node(H, n)
        attrs_copy = attrs.copy() if attrs else {}
        attrs_copy["_hif_id"] = n

        type_name = attrs_copy.get("type", "")

        is_simple = True
        for k in attrs_copy:
            if k not in ["kind", "value", "type", "_hif_id"]:
                is_simple = False
                break

        if is_simple and attrs_copy.get("kind") == "scalar" and attrs_copy.get("value") == type_name:
            spider_types_list.append(Ty(type_name))
        else:
            try:
                json_str = json.dumps(attrs_copy, sort_keys=True, default=str)
                spider_types_list.append(Ty(Ob(json_str)))
            except TypeError:
                name = str(type_name)
                spider_types_list.append(Ty(name))

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

            e_idx = H[1].graph.get("incidence_pair_index", 1)
            v_idx = H[0].graph.get("incidence_pair_index", 0)

            def is_edge(x): return isinstance(x, tuple) and len(x)==2 and x[1] == e_idx
            def is_node(x): return isinstance(x, tuple) and len(x)==2 and x[1] == v_idx

            real_edge_id = None
            real_node_id = None

            if is_edge(u): real_edge_id = u[0]
            if is_node(u): real_node_id = u[0]
            if is_edge(v): real_edge_id = v[0]
            if is_node(v): real_node_id = v[0]

            if real_edge_id is None:
                if u in all_edges: real_edge_id = u
                elif v in all_edges: real_edge_id = v
            if real_node_id is None:
                if u in node_to_idx: real_node_id = u
                elif v in node_to_idx: real_node_id = v

            if real_edge_id is not None and real_node_id is not None:
                if real_edge_id not in incidences_by_edge:
                    incidences_by_edge[real_edge_id] = []
                incidences_by_edge[real_edge_id].append((real_node_id, key, data))

    boxes = []
    box_wires_list = []

    sorted_edges = sorted(all_edges, key=lambda x: str(x))

    boundary_edge_id = None
    for e in sorted_edges:
        attrs = hif_edge(H, e)
        if attrs.get("kind") == "boundary" or str(e) == "_boundary":
            boundary_edge_id = e
            break

    for e in sorted_edges:
        if e == boundary_edge_id:
            continue

        attrs = hif_edge(H, e)
        attrs_copy = attrs.copy() if attrs else {}
        attrs_copy["_hif_id"] = e

        incs = incidences_by_edge.get(e, [])
        if not incs:
             incs = list(hif_edge_incidences(H, e))

        def sort_key(inc):
            if len(inc) == 4:
                data = inc[3]
                key = inc[2]
                node_id = inc[1]
            else:
                data = inc[2]
                key = inc[1]
                node_id = inc[0]

            role = data.get("role", "")
            key_str = str(key)
            n_idx = node_to_idx.get(node_id, -1)
            idx_attr = data.get("index", -1)
            role_prio = 0 if role == 'dom' else 1 if role == 'cod' else 2
            return (role_prio, idx_attr, key_str, n_idx)

        sorted_incs = sorted(incs, key=sort_key)

        b_dom_wires = []
        b_cod_wires = []
        inc_metadata = []

        for i, inc in enumerate(sorted_incs):
            if len(inc) == 4:
                node_id = inc[1]
                data = inc[3]
                key = inc[2]
            else:
                node_id = inc[0]
                data = inc[2]
                key = inc[1]

            if node_id not in node_to_idx:
                continue

            node_idx = node_to_idx[node_id]
            role = data.get("role")

            meta = {
                'role': role,
                'key': key,
                'attrs': data,
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

        name = attrs.get("name") or attrs.get("kind") or str(e)

        box_data = {
            "attributes": attrs_copy,
            "incidences": inc_metadata
        }

        box = Box(name, b_dom, b_cod, data=box_data)
        boxes.append(box)
        box_wires_list.append((tuple(b_dom_wires), tuple(b_cod_wires)))

    if boundary_edge_id is not None:
        incs = incidences_by_edge.get(boundary_edge_id, [])
        if not incs:
             incs = list(hif_edge_incidences(H, boundary_edge_id))

        def sort_key_boundary(inc):
            if len(inc) == 4:
                data = inc[3]
                key = inc[2]
                node_id = inc[1]
            else:
                data = inc[2]
                key = inc[1]
                node_id = inc[0]
            role = data.get("role", "")
            idx_attr = data.get("index", -1)
            key_str = str(key)
            n_idx = node_to_idx.get(node_id, -1)
            role_prio = 0 if role == 'dom' else 1 if role == 'cod' else 2
            return (role_prio, idx_attr, key_str, n_idx)

        sorted_incs = sorted(incs, key=sort_key_boundary)

        for inc in sorted_incs:
            if len(inc) == 4:
                node_id = inc[1]
                data = inc[3]
            else:
                node_id = inc[0]
                data = inc[2]

            if node_id not in node_to_idx:
                continue

            node_idx = node_to_idx[node_id]
            role = data.get("role")

            if role == "dom":
                dom_wires.append(node_idx)
            elif role == "cod":
                cod_wires.append(node_idx)

        for s in dom_wires:
            dom = dom @ spider_types[s]
        for s in cod_wires:
            cod = cod @ spider_types[s]

    wires = (tuple(dom_wires), tuple(box_wires_list), tuple(cod_wires))

    return Hypergraph(dom, cod, tuple(boxes), wires, spider_types)
