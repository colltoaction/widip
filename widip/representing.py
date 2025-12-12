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

    def next_id():
        return next(id_counter)

    # We construct a stream -> document -> sequence -> [boxes...]
    # But wait, if "box names use kinds as names", maybe the top-level structure is also boxes?
    # No, nx_yaml requires root to be Stream.
    # So we must wrap the diagram in Stream -> Document -> Sequence (or whatever the diagram represents).

    # Or maybe the diagram *is* the document content?

    # Let's keep the wrapper structure but use box names as kinds for the content.

    stream_id = next_id() # 0
    e_stream = next_id()  # 1
    hif_add_node(hif_g, stream_id, kind="stream")
    hif_add_edge(hif_g, e_stream, kind="event")
    hif_add_incidence(hif_g, e_stream, stream_id, key="start")

    doc_id = next_id() # 2
    e_doc = next_id()  # 3
    hif_add_node(hif_g, doc_id, kind="document")
    hif_add_edge(hif_g, e_doc, kind="event")
    hif_add_incidence(hif_g, e_doc, doc_id, key="start")

    hif_add_incidence(hif_g, e_doc, stream_id, key="next")
    hif_add_incidence(hif_g, e_doc, stream_id, key="end")

    # Should we wrap in a Sequence?
    # If the diagram is a list of boxes, Sequence is appropriate.
    # If the diagram contains a single box "mapping", then Sequence might be redundant?
    # But hg.boxes is a list.

    seq_id = next_id() # 4
    e_seq_node = next_id() # 5
    hif_add_node(hif_g, seq_id, kind="sequence")
    hif_add_edge(hif_g, e_seq_node, kind="event")
    hif_add_incidence(hif_g, e_seq_node, seq_id, key="start")

    hif_add_incidence(hif_g, e_seq_node, doc_id, key="next")
    hif_add_incidence(hif_g, e_seq_node, doc_id, key="end")

    spider_map = {} # idx -> (node_id, edge_id)

    def get_spider(idx):
        if idx not in spider_map:
            sid = next_id()
            eid = next_id()
            # Spiders are wires. Should they have a kind?
            # "scalar" is generic.
            # Maybe use "scalar" for wires.
            hif_add_node(hif_g, sid, kind="scalar", value=None, tag=f"!wire_{idx}", anchor=f"wire_{idx}")
            hif_add_edge(hif_g, eid, kind="event")
            hif_add_incidence(hif_g, eid, sid, key="start")
            spider_map[idx] = (sid, eid)
        return spider_map[idx]

    dom_wires, boxes_wires, cod_wires = hg.wires
    prev_node = seq_id
    last_seq_edge = None

    for i, (box, (box_dom_spiders, box_cod_spiders)) in enumerate(zip(hg.boxes, boxes_wires)):
        box_id = next_id()
        e_box = next_id()

        # USE BOX NAME AS KIND
        kind = box.name
        # Note: If box.name is not valid kind, serialization will fail.

        # Tags/Values?
        # If kind is "scalar", it needs a value?
        # If kind is "mapping", it needs keys.

        attributes = {"kind": kind}
        if hasattr(box, "data") and isinstance(box.data, dict):
            attributes.update(box.data)

        hif_add_node(hif_g, box_id, **attributes)
        hif_add_edge(hif_g, e_box, kind="event")
        hif_add_incidence(hif_g, e_box, box_id, key="start")

        last_seq_edge = e_box

        if i == 0:
            hif_add_incidence(hif_g, e_box, seq_id, key="next")
        else:
            hif_add_incidence(hif_g, e_box, prev_node, key="forward") # sequence connection

        prev_node = box_id

        # Handle connectivity.
        # If kind="mapping", we expect keys.
        # If kind="scalar", we expect value (in attributes).
        # If kind="sequence", we expect items.

        # How to map wires?
        # If the user diagram is AST, maybe wires are implicit or represented differently?
        # But we have `dom_wires` and `cod_wires`.

        # If kind="mapping", we can map inputs/outputs as keys?
        if kind == "mapping":
            # Add inputs/outputs as keys
            keys = []
            for j, spider_idx in enumerate(box_dom_spiders):
                keys.append((f"dom_{j}", spider_idx))
            for j, spider_idx in enumerate(box_cod_spiders):
                keys.append((f"cod_{j}", spider_idx))

            prev_key_node = box_id
            last_key_edge = None

            if not keys:
                 # Empty mapping handling
                 e_dummy = next_id()
                 hif_add_edge(hif_g, e_dummy, kind="event")
                 hif_add_incidence(hif_g, e_dummy, box_id, key="next")
                 hif_add_incidence(hif_g, e_dummy, box_id, key="end")

            for k_idx, (k_name, sp_idx) in enumerate(keys):
                key_id = next_id()
                e_key = next_id()

                hif_add_node(hif_g, key_id, kind="scalar", value=k_name)
                hif_add_edge(hif_g, e_key, kind="event")
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

        # If kind="scalar", we just emit it. (Assuming value is in attributes)
        # If kind="sequence", we would need to emit items?

    if last_seq_edge:
        hif_add_incidence(hif_g, last_seq_edge, seq_id, key="end")
    else:
        e_dummy = next_id()
        hif_add_edge(hif_g, e_dummy, kind="event")
        hif_add_incidence(hif_g, e_dummy, seq_id, key="next")
        hif_add_incidence(hif_g, e_dummy, seq_id, key="end")

    return hif_g
