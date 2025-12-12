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

    # Pattern: Node N, Edge N+1. Edge N+1 starts at Node N.
    # Parent links to Edge N+1.

    # 0: Stream
    stream_id = next_id() # 0
    e_stream = next_id()  # 1
    hif_add_node(hif_g, stream_id, kind="stream")
    hif_add_edge(hif_g, e_stream, kind="event")
    hif_add_incidence(hif_g, e_stream, stream_id, key="start")

    # 2: Document
    doc_id = next_id() # 2
    e_doc = next_id()  # 3
    hif_add_node(hif_g, doc_id, kind="document")
    hif_add_edge(hif_g, e_doc, kind="event")
    hif_add_incidence(hif_g, e_doc, doc_id, key="start")

    # Connect Stream -> Doc
    hif_add_incidence(hif_g, e_doc, stream_id, key="next")
    hif_add_incidence(hif_g, e_doc, stream_id, key="end")

    # 4: Sequence
    seq_id = next_id() # 4
    e_seq_node = next_id() # 5 (Edge belonging to Seq node)
    hif_add_node(hif_g, seq_id, kind="sequence")
    hif_add_edge(hif_g, e_seq_node, kind="event")
    hif_add_incidence(hif_g, e_seq_node, seq_id, key="start")

    # Connect Doc -> Seq
    hif_add_incidence(hif_g, e_seq_node, doc_id, key="next")
    hif_add_incidence(hif_g, e_seq_node, doc_id, key="end")

    # Spiders need to be allocated. But if we want interleaving, we should allocate them
    # when they are encountered in the tree traversal?
    # But spiders are referenced multiple times.
    # However, anchors in YAML are usually defined at first occurrence.
    # If we treat spiders as values in the mapping, they are nodes in the tree.
    # Subsequent references are aliases.
    # nx_yaml handles anchors/aliases if graph structure is DAG.

    # So we can allocate spider nodes on demand, BUT they must fit the N, N+1 pattern?
    # If they are just referenced, maybe their ID doesn't matter as much as long as they have their own Edge?
    # Let's verify: In `inspect_mapping.py`, Value node 8 has Edge 9.
    # If I reuse spider node 8 later, it still has Edge 9.

    # So I need a way to retrieve or create spider node.
    spider_map = {} # spider_idx -> (node_id, edge_id)

    def get_spider(idx):
        if idx not in spider_map:
            sid = next_id()
            eid = next_id()
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

        tag = f"!{box.name}"
        hif_add_node(hif_g, box_id, kind="mapping", tag=tag)
        hif_add_edge(hif_g, e_box, kind="event")
        hif_add_incidence(hif_g, e_box, box_id, key="start")

        last_seq_edge = e_box

        if i == 0:
            hif_add_incidence(hif_g, e_box, seq_id, key="next")
        else:
            hif_add_incidence(hif_g, e_box, prev_node, key="forward") # Connect to previous box ID?
            # Wait, in sequence, items are linked.
            # Item 1 -> forward -> Edge 2 -> Item 2
            # But here `e_box` belongs to `box_id`.
            # So `prev_node` should link to `e_box`.
            # But `prev_node` is a Node.

            # Inspect sequence in `inspect_hif.py` (hello-world was !echo, just a scalar).
            # Shell.yaml has sequence.
            # I can't check shell.yaml structure easily now without running script.

            # But based on mapping logic:
            # Key -> forward -> Edge -> Value.
            # So Sequence:
            # Item 1 -> forward -> Edge -> Item 2.
            pass

        hif_add_incidence(hif_g, e_box, prev_node, key="forward" if i > 0 else "next")
        # Wait, if i=0: seq_id -> next -> e_box. Correct.
        # If i>0: prev_node -> forward -> e_box. Correct.

        prev_node = box_id

        # Keys
        keys = []
        for j, spider_idx in enumerate(box_dom_spiders):
            keys.append((f"dom_{j}", spider_idx))
        for j, spider_idx in enumerate(box_cod_spiders):
            keys.append((f"cod_{j}", spider_idx))

        prev_key_node = box_id
        last_key_edge = None

        if not keys:
             # Empty mapping requires next/end pointing to something?
             # Or maybe just NO next/end edges means empty?
             # But hello-world mapping had end on edge 9.
             # If empty, maybe I need a dummy edge.
             pass

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
                # Previous Value Node -> forward -> e_key
                hif_add_incidence(hif_g, e_key, prev_key_node, key="forward")

            # Value
            spider_node, e_spider = get_spider(sp_idx)

            # Key -> forward -> Edge -> Value
            # But Edge must be `e_spider`?
            # `e_spider` is the edge belonging to `spider_node`.
            # So we link Key -> forward -> e_spider.

            hif_add_incidence(hif_g, e_spider, key_id, key="forward")

            # Update prev_key_node to be the Value node
            prev_key_node = spider_node

            # Also, the last item in mapping needs 'end' from Mapping node?
            # In `inspect_mapping`: Edge 9 (Value Edge) has 'end' from Mapping (4).

            # So `e_spider` needs 'end' from `box_id` IF it is the last value?
            # Yes.

            if k_idx == len(keys) - 1:
                hif_add_incidence(hif_g, e_spider, box_id, key="end")

    if last_seq_edge:
        hif_add_incidence(hif_g, last_seq_edge, seq_id, key="end")
    else:
        # Empty sequence
        # Create a dummy edge?
        # But dummy edge needs a node?
        # If I create a dummy node.
        pass

    return hif_g
