from nx_hif.hif import hif_create, hif_add_node, hif_add_edge, hif_add_incidence
from discopy.markov import Diagram as MarkovDiagram, Ty as MarkovTy, Box as MarkovBox
from discopy.closed import Diagram as ClosedDiagram
from discopy.monoidal import Box, Layer
import itertools

def hif_new_edge(G, **attr):
    _, E, _ = G
    edge = E.number_of_nodes()
    hif_add_edge(G, edge, **attr)
    return edge

def hif_new_node(G, **attr):
    V, _, _ = G
    node = V.number_of_nodes()
    hif_add_node(G, node, **attr)
    return node

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

    # 0: Stream
    stream_id = hif_new_node(hif_g, kind="stream")
    e_stream = hif_new_edge(hif_g, kind="event")
    hif_add_incidence(hif_g, e_stream, stream_id, key="start")

    # 1: Document
    doc_id = hif_new_node(hif_g, kind="document")
    e_doc = hif_new_edge(hif_g, kind="event")
    hif_add_incidence(hif_g, e_doc, doc_id, key="start")

    hif_add_incidence(hif_g, e_doc, stream_id, key="next")
    hif_add_incidence(hif_g, e_doc, stream_id, key="end")

    # 2: Sequence
    seq_id = hif_new_node(hif_g, kind="sequence")
    e_seq_node = hif_new_edge(hif_g, kind="event")
    hif_add_incidence(hif_g, e_seq_node, seq_id, key="start")

    hif_add_incidence(hif_g, e_seq_node, doc_id, key="next")
    hif_add_incidence(hif_g, e_seq_node, doc_id, key="end")

    spider_map = {} # idx -> (node_id, edge_id)

    def get_spider(idx):
        if idx not in spider_map:
            sid = hif_new_node(hif_g, kind="scalar", value=None, tag=f"!wire_{idx}", anchor=f"wire_{idx}")
            eid = hif_new_edge(hif_g, kind="event")
            hif_add_incidence(hif_g, eid, sid, key="start")
            spider_map[idx] = (sid, eid)
        return spider_map[idx]

    dom_wires, boxes_wires, cod_wires = hg.wires
    prev_node = seq_id
    last_seq_edge = None

    for i, (box, (box_dom_spiders, box_cod_spiders)) in enumerate(zip(hg.boxes, boxes_wires)):
        kind = box.name
        attributes = {"kind": kind}
        if hasattr(box, "data") and isinstance(box.data, dict):
            attributes.update(box.data)

        box_id = hif_new_node(hif_g, **attributes)
        e_box = hif_new_edge(hif_g, kind="event")
        hif_add_incidence(hif_g, e_box, box_id, key="start")

        last_seq_edge = e_box

        if i == 0:
            hif_add_incidence(hif_g, e_box, seq_id, key="next")
        else:
            hif_add_incidence(hif_g, e_box, prev_node, key="forward")

        prev_node = box_id

        if kind == "mapping":
            keys = []
            for j, spider_idx in enumerate(box_dom_spiders):
                keys.append((f"dom_{j}", spider_idx))
            for j, spider_idx in enumerate(box_cod_spiders):
                keys.append((f"cod_{j}", spider_idx))

            prev_key_node = box_id
            last_key_edge = None

            if not keys:
                 e_dummy = hif_new_edge(hif_g, kind="event")
                 hif_add_incidence(hif_g, e_dummy, box_id, key="next")
                 hif_add_incidence(hif_g, e_dummy, box_id, key="end")

            for k_idx, (k_name, sp_idx) in enumerate(keys):
                key_id = hif_new_node(hif_g, kind="scalar", value=k_name)
                e_key = hif_new_edge(hif_g, kind="event")
                hif_add_incidence(hif_g, e_key, key_id, key="start")

                last_key_edge = e_key

                if k_idx == 0:
                    hif_add_incidence(hif_g, e_key, box_id, key="next")
                else:
                    hif_add_incidence(hif_g, e_key, prev_key_node, key="forward")

                spider_node, e_spider = get_spider(sp_idx)
                hif_add_incidence(hif_g, e_spider, key_id, key="forward")

                prev_key_node = spider_node

                if k_idx == len(keys) - 1:
                    hif_add_incidence(hif_g, e_spider, box_id, key="end")

    if last_seq_edge:
        hif_add_incidence(hif_g, last_seq_edge, seq_id, key="end")
    else:
        e_dummy = hif_new_edge(hif_g, kind="event")
        hif_add_incidence(hif_g, e_dummy, seq_id, key="next")
        hif_add_incidence(hif_g, e_dummy, seq_id, key="end")

    # Dummy edge at the end to satisfy nx_yaml peeking
    hif_new_edge(hif_g, kind="dummy")

    return hif_g
