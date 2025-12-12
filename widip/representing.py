from nx_hif.hif import hif_create, hif_add_node, hif_add_edge, hif_add_incidence
from discopy.markov import Diagram as MarkovDiagram, Ty as MarkovTy, Box as MarkovBox
from discopy.closed import Diagram as ClosedDiagram
from discopy.monoidal import Box, Layer
import itertools

def convert_to_markov(diagram):
    def convert_ty(ty):
        return MarkovTy(*[str(x) for x in ty])

    def convert_box(box):
        return MarkovBox(box.name, convert_ty(box.dom), convert_ty(box.cod), data=box.data)

    new_boxes = [convert_box(b) for b in diagram.boxes]
    new_dom = convert_ty(diagram.dom)
    new_cod = convert_ty(diagram.cod)

    new_layers = []

    for layer in diagram.inside:
        if hasattr(layer, 'left'):
            l = convert_ty(layer.left)
            r = convert_ty(layer.right)
            b = convert_box(layer.box)
            new_layers.append(Layer(l, b, r))
        else:
             try:
                 l, b, r = layer.boxes_or_types
                 new_layers.append(Layer(convert_ty(l), convert_box(b), convert_ty(r)))
             except:
                 pass

    return MarkovDiagram(tuple(new_layers), new_dom, new_cod)

def discopy_to_hif(diagram):
    if not hasattr(diagram, "to_hypergraph"):
        try:
            diagram = convert_to_markov(diagram)
        except Exception as e:
            raise NotImplementedError(f"Cannot convert diagram to hypergraph: {e}")

    hg = diagram.to_hypergraph()
    hif_g = hif_create()

    id_counter = itertools.count()

    def next_node_id():
        return next(id_counter)

    def next_edge_id():
        return next(id_counter)

    stream_id = next_node_id() # 0
    e_stream_start = next_edge_id() # 1

    hif_add_node(hif_g, stream_id, kind="stream")
    hif_add_edge(hif_g, e_stream_start, kind="event")
    hif_add_incidence(hif_g, e_stream_start, stream_id, key="start")

    doc_id = next_node_id() # 2
    e_stream_doc = next_edge_id() # 3

    hif_add_node(hif_g, doc_id, kind="document")
    hif_add_edge(hif_g, e_stream_doc, kind="event")
    hif_add_incidence(hif_g, e_stream_doc, stream_id, key="next")
    hif_add_incidence(hif_g, e_stream_doc, stream_id, key="end")
    hif_add_incidence(hif_g, e_stream_doc, doc_id, key="start")

    seq_id = next_node_id() # 4
    e_doc_seq = next_edge_id() # 5

    hif_add_node(hif_g, seq_id, kind="sequence")
    hif_add_edge(hif_g, e_doc_seq, kind="event")
    hif_add_incidence(hif_g, e_doc_seq, doc_id, key="next")
    hif_add_incidence(hif_g, e_doc_seq, doc_id, key="end")
    hif_add_incidence(hif_g, e_doc_seq, seq_id, key="start")

    spider_to_node = {}

    def get_spider_node(idx, ty):
        if idx not in spider_to_node:
            sid = next_node_id()
            hif_add_node(hif_g, sid, kind="scalar", value=None, tag=f"!wire_{idx}", anchor=f"wire_{idx}")
            spider_to_node[idx] = sid
        return spider_to_node[idx]

    dom_wires, boxes_wires, cod_wires = hg.wires
    prev_node = seq_id
    last_seq_edge = None

    for i, (box, (box_dom_spiders, box_cod_spiders)) in enumerate(zip(hg.boxes, boxes_wires)):
        box_id = next_node_id()
        tag = f"!{box.name}"

        # NOTE: nx_yaml might not output tag for Mapping if it's implicit or confusion?
        # But if I look at yaml dump, it seems to have output keys dom_0: cod_0
        # This implies it rendered the mapping content.
        # But lost the tag?
        # Maybe because box_id mapping node doesn't have explicit style/tag logic handled correctly?
        # Or maybe I should check if tag is set correctly.

        hif_add_node(hif_g, box_id, kind="mapping", tag=tag)

        e_seq = next_edge_id()
        hif_add_edge(hif_g, e_seq, kind="event")
        last_seq_edge = e_seq

        if i == 0:
            hif_add_incidence(hif_g, e_seq, seq_id, key="next")
        else:
            hif_add_incidence(hif_g, e_seq, prev_node, key="forward")

        hif_add_incidence(hif_g, e_seq, box_id, key="start")
        prev_node = box_id

        # Handle mapping keys
        keys = []
        for j, spider_idx in enumerate(box_dom_spiders):
            keys.append((f"dom_{j}", spider_idx))
        for j, spider_idx in enumerate(box_cod_spiders):
            keys.append((f"cod_{j}", spider_idx))

        prev_key_node = box_id
        last_key_edge = None

        if not keys:
             e_dummy = next_edge_id()
             hif_add_edge(hif_g, e_dummy, kind="event")
             hif_add_incidence(hif_g, e_dummy, box_id, key="next")
             hif_add_incidence(hif_g, e_dummy, box_id, key="end")

        for k_idx, (k_name, sp_idx) in enumerate(keys):
            key_id = next_node_id()
            hif_add_node(hif_g, key_id, kind="scalar", value=k_name)

            e_key = next_edge_id()
            hif_add_edge(hif_g, e_key, kind="event")
            last_key_edge = e_key

            if k_idx == 0:
                hif_add_incidence(hif_g, e_key, box_id, key="next")
            else:
                hif_add_incidence(hif_g, e_key, prev_key_node, key="forward")

            hif_add_incidence(hif_g, e_key, key_id, key="start")

            # Value (Spider)
            spider_node = get_spider_node(sp_idx, None)

            e_val = next_edge_id()
            hif_add_edge(hif_g, e_val, kind="event")
            hif_add_incidence(hif_g, e_val, key_id, key="next")
            hif_add_incidence(hif_g, e_val, key_id, key="end")
            hif_add_incidence(hif_g, e_val, spider_node, key="start")

            prev_key_node = key_id

        if last_key_edge:
             hif_add_incidence(hif_g, last_key_edge, box_id, key="end")

    if last_seq_edge:
        hif_add_incidence(hif_g, last_seq_edge, seq_id, key="end")
    else:
        # Empty sequence: need 'next' and 'end' pointing to empty?
        # Create dummy edge
        e_dummy = next_edge_id()
        hif_add_edge(hif_g, e_dummy, kind="event")
        hif_add_incidence(hif_g, e_dummy, seq_id, key="next")
        hif_add_incidence(hif_g, e_dummy, seq_id, key="end")

    return hif_g
