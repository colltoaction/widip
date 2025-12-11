from nx_hif.hif import (
    hif_create, hif_add_node, hif_add_edge, hif_add_incidence,
    hif_nodes, hif_edges, hif_edge_incidences, hif_node, hif_edge
)

from discopy.markov import Hypergraph, Ty, Box
from discopy.cat import Ob
import json

class HIFOb(Ob):
    """
    A DisCoPy Object that wraps HIF node attributes.
    """
    def __init__(self, name="", data=None):
        self.data = data or {}
        # If name is empty but data has 'type', use it.
        if not name and 'type' in self.data:
            name = str(self.data['type'])
        super().__init__(name)

    def __eq__(self, other):
        if isinstance(other, HIFOb):
            return self.name == other.name and self.data == other.data
        return super().__eq__(other)

    def __repr__(self):
        return f"HIFOb({self.name}, {self.data})"

    def __hash__(self):
        # Make hashable for Ty
        return hash((self.name, tuple(sorted(self.data.items()))))

def discopy_to_hif(diagram: Hypergraph):
    """
    Convert a discopy.markov.Hypergraph to an nx_hif structure.
    Does NOT add explicit 'dom'/'cod' edges for the boundary.
    Instead, marks boundary spiders with attributes.
    """
    H = hif_create()

    # Map spider indices to node IDs (integers)
    # diagram.spider_types is a tuple.
    for i in range(diagram.n_spiders):
        t = diagram.spider_types[i] if i < len(diagram.spider_types) else Ty()

        # Extract attributes
        attrs = {}
        # Check if t contains HIFOb. t.inside is the tuple of objects.
        if len(t.inside) == 1 and isinstance(t.inside[0], HIFOb):
             attrs = t.inside[0].data.copy()
             # Ensure 'type' is set if needed
             if "type" not in attrs and t.inside[0].name:
                 attrs["type"] = t.inside[0].name
        else:
             # Standard Ty
             if t.name:
                 attrs["type"] = t.name

        # Check boundary
        # wires[0] is list of spider indices connected to dom
        indices_dom = [idx for idx, s in enumerate(diagram.wires[0]) if s == i]
        if indices_dom:
             attrs["dom_ports"] = indices_dom

        indices_cod = [idx for idx, s in enumerate(diagram.wires[2]) if s == i]
        if indices_cod:
             attrs["cod_ports"] = indices_cod

        hif_add_node(H, i, **attrs)

    # Add edges for boxes
    # wires[1] is list of (dom_wires, cod_wires) for each box.
    for i, (box, (dom_wires, cod_wires)) in enumerate(zip(diagram.boxes, diagram.wires[1])):
        edge_id = f"box_{i}"

        # Attributes
        attrs = {}
        # If box.data contains 'attributes', use them (roundtrip from HIF)
        if isinstance(box.data, dict) and "attributes" in box.data:
            attrs.update(box.data["attributes"])
        else:
            # Reconstruct attributes from standard box
            if box.name:
                attrs["name"] = box.name
            if box.dom.name:
                attrs["dom"] = box.dom.name
            if box.cod.name:
                attrs["cod"] = box.cod.name

        hif_add_edge(H, edge_id, **attrs)

        # Incidences
        # If we have stored incidence metadata, use it to restore keys/roles.
        inc_meta = []
        if isinstance(box.data, dict) and "incidences" in box.data:
            inc_meta = box.data["incidences"]

        def get_meta(role, index):
            for m in inc_meta:
                if m.get('port_index') == index and (m.get('role') == role or (role=='cod' and m.get('role') is None)):
                    return m
            return None

        # Dom wires (inputs)
        for j, spider_idx in enumerate(dom_wires):
            meta = get_meta("dom", j)
            if meta:
                meta_attrs = meta.get('attrs', {}).copy()
                # Remove role from attrs if present, as we pass it explicitly
                meta_attrs.pop('role', None)
                hif_add_incidence(H, edge_id, spider_idx, key=meta.get('key'), role=meta.get('role'), **meta_attrs)
            else:
                # Default behavior
                hif_add_incidence(H, edge_id, spider_idx, role="dom", index=j)

        # Cod wires (outputs)
        for j, spider_idx in enumerate(cod_wires):
            meta = get_meta("cod", j)
            if meta:
                meta_attrs = meta.get('attrs', {}).copy()
                meta_attrs.pop('role', None)
                hif_add_incidence(H, edge_id, spider_idx, key=meta.get('key'), role=meta.get('role'), **meta_attrs)
            else:
                hif_add_incidence(H, edge_id, spider_idx, role="cod", index=j)

    return H

def hif_to_discopy(H):
    """
    Convert an nx_hif structure to a discopy.markov.Hypergraph.
    """
    all_nodes = list(hif_nodes(H))
    all_edges = list(hif_edges(H))

    # Sort nodes
    sorted_nodes = sorted(all_nodes, key=lambda x: str(x))
    node_to_idx = {n: i for i, n in enumerate(sorted_nodes)}

    spider_types_list = []
    dom_ports_map = {} # port_index -> spider_idx
    cod_ports_map = {} # port_index -> spider_idx

    for i, n in enumerate(sorted_nodes):
        attrs = hif_node(H, n)
        # Wrap attrs in HIFOb
        name = str(attrs.get("type", ""))
        spider_types_list.append(Ty(HIFOb(name, attrs)))

        if "dom_ports" in attrs:
            for p_idx in attrs["dom_ports"]:
                dom_ports_map[p_idx] = i
        if "cod_ports" in attrs:
            for p_idx in attrs["cod_ports"]:
                cod_ports_map[p_idx] = i

    spider_types = tuple(spider_types_list)

    # Construct Dom/Cod wires
    dom_wires = []
    if dom_ports_map:
        max_dom = max(dom_ports_map.keys())
        dom_wires = [dom_ports_map.get(k, 0) for k in range(max_dom + 1)]

    cod_wires = []
    if cod_ports_map:
        max_cod = max(cod_ports_map.keys())
        cod_wires = [cod_ports_map.get(k, 0) for k in range(max_cod + 1)]

    # Dom/Cod Types
    dom = Ty()
    for s in dom_wires:
        dom = dom @ spider_types[s]

    cod = Ty()
    for s in cod_wires:
        cod = cod @ spider_types[s]

    # Pre-process incidences from H[2] (incidence graph)
    incidences_by_edge = {} # edge_id -> list of (node_id, key, attrs)

    I = H[2]
    # Check if we have edges in I
    if hasattr(I, "edges"):
        for u, v, key, data in I.edges(data=True, keys=True):
            edge_id = None
            node_id = None

            # Check u
            if u in node_to_idx: node_id = u
            elif u in all_edges: edge_id = u
            elif isinstance(u, tuple) and len(u) == 2:
                # Assuming (id, 1) is edge, (id, 0) is node
                if u[1] == 1: edge_id = u[0]
                elif u[1] == 0: node_id = u[0]

            # Check v
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

        # Get incidences for this edge
        incs = []
        if e in incidences_by_edge:
            for node, key, data in incidences_by_edge[e]:
                incs.append((e, node, key, data))
        else:
             # Try standard accessor as fallback
             incs = list(hif_edge_incidences(H, e))

        # Sort incidences
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
            "attributes": attrs,
            "incidences": inc_metadata
        }

        box = Box(name, b_dom, b_cod, data=box_data)
        boxes.append(box)
        box_wires_list.append((tuple(b_dom_wires), tuple(b_cod_wires)))

    wires = (tuple(dom_wires), tuple(box_wires_list), tuple(cod_wires))

    return Hypergraph(dom, cod, tuple(boxes), wires, spider_types)
