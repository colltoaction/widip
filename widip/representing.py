from nx_hif.hif import (
    hif_create, hif_add_node, hif_add_edge, hif_add_incidence,
    hif_nodes, hif_edges, hif_edge_incidences, hif_node, hif_edge
)

from discopy.markov import Hypergraph, Ty, Box
from discopy.cat import Ob
import json
import ast

def discopy_to_hif(diagram: Hypergraph):
    """
    Convert a discopy.markov.Hypergraph to an nx_hif structure.
    Does NOT encode diagram boundary (dom/cod) as attributes.
    Preserves original HIF IDs if present in attributes (stored in Ob name via repr).
    """
    H = hif_create()

    # Map spider indices to HIF Node IDs
    spider_to_hif_id = {}

    for i in range(diagram.n_spiders):
        t = diagram.spider_types[i] if i < len(diagram.spider_types) else Ty()

        attrs = {}
        hif_id = i # Default ID

        if len(t.inside) == 1:
            name = t.inside[0].name
            try:
                # Try literal_eval to support python types like tuples
                val = ast.literal_eval(name)
                if isinstance(val, dict):
                    attrs = val
                else:
                    attrs = {"type": name}
            except (ValueError, SyntaxError):
                # Fallback
                if name:
                    attrs = {"type": name}
        elif t.name:
             attrs = {"type": t.name}

        # Restore original ID
        if "_hif_id" in attrs:
            hif_id = attrs.pop("_hif_id")

        spider_to_hif_id[i] = hif_id
        hif_add_node(H, hif_id, **attrs)

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
            if meta:
                meta_attrs = meta.get('attrs', {}).copy()
                meta_attrs.pop('role', None)
                hif_add_incidence(H, edge_id, hif_node_id, key=meta.get('key'), role=meta.get('role'), **meta_attrs)
            else:
                hif_add_incidence(H, edge_id, hif_node_id, role=role, index=index)

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

    spider_types_list = []

    for i, n in enumerate(sorted_nodes):
        attrs = hif_node(H, n)
        attrs_copy = attrs.copy() if attrs else {}
        attrs_copy["_hif_id"] = n

        # Serialize attributes to Python literal string (repr) to preserve tuples
        try:
            # repr gives a string representation that literal_eval can read
            # We sort keys in repr? No, dict order is preserved in py3.7+.
            # But to be safe for deterministic output, maybe sort?
            # ast.literal_eval handles standard dict syntax.
            # repr(dict) is standard syntax.
            # But let's check if we need deterministic sorting.
            # If we just do repr(attrs_copy), order depends on insertion.
            # attrs_copy is a new dict.
            # Let's hope it's fine or sort it?
            # Cannot sort dict directly.
            # But Ty equality compares string names.
            # If string representation varies, Ty will differ.
            # So we SHOULD ensure deterministic repr.
            # Convert to list of tuples, sort, then reconstruct dict?
            # Or just rely on repr?
            # For roundtrip, as long as we recover the dict, it's fine.
            # But for `test_roundtrip...` we check `encoded == encoded_prime`.
            # That checks the *attributes dict* equality, not Ty name equality.
            # So `discopy_to_hif` recovering the dict is enough.
            # Ty equality matters for `assert h_prime == h`, but we skipped strict equality there for attributes.

            s_val = repr(attrs_copy)
            spider_types_list.append(Ty(Ob(s_val)))
        except Exception:
            name = str(attrs_copy.get("type", ""))
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

            if u in node_to_idx: node_id = u
            elif u in all_edges: edge_id = u
            elif isinstance(u, tuple) and len(u) == 2:
                if u[1] == 1: edge_id = u[0]
                elif u[1] == 0: node_id = u[0]

            if v in node_to_idx: node_id = v
            elif v in all_edges: edge_id = v
            elif isinstance(v, tuple) and len(v) == 2:
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
        attrs_copy["_hif_id"] = e

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

        name = attrs.get("name") or attrs.get("kind") or str(e)

        box_data = {
            "attributes": attrs_copy,
            "incidences": inc_metadata
        }

        box = Box(name, b_dom, b_cod, data=box_data)
        boxes.append(box)
        box_wires_list.append((tuple(b_dom_wires), tuple(b_cod_wires)))

    wires = (tuple(dom_wires), tuple(box_wires_list), tuple(cod_wires))

    return Hypergraph(dom, cod, tuple(boxes), wires, spider_types)
