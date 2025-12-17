from discopy.hypergraph import Hypergraph
from nx_hif.hif import hif_create, hif_new_node, hif_new_edge, hif_add_incidence


def discopy_to_hif(hg: Hypergraph):
    hif_hg = hif_create()
    
    # Create spiders (edges)
    spider_to_eid = {}
    for i in range(hg.n_spiders):
        eid = hif_new_edge(hif_hg, kind="spider")
        spider_to_eid[i] = eid
        
    # Create boundary
    boundary_id = hif_new_node(hif_hg, kind="boundary")
    
    # Connect boundary
    dom_wires = hg.wires[0]
    for i, spider_idx in enumerate(dom_wires):
        eid = spider_to_eid[spider_idx]
        hif_add_incidence(hif_hg, eid, boundary_id, role="dom", index=i, key=None)
        
    cod_wires = hg.wires[2]
    for i, spider_idx in enumerate(cod_wires):
        eid = spider_to_eid[spider_idx]
        hif_add_incidence(hif_hg, eid, boundary_id, role="cod", index=i, key=None)
        
    # Create boxes
    box_wires = hg.wires[1]
    for i, box in enumerate(hg.boxes):
        data = box.data.copy() if box.data else {}
        data["kind"] = box.name
        nid = hif_new_node(hif_hg, **data)
        
        ins, outs = box_wires[i]
        for idx, spider_idx in enumerate(ins):
            eid = spider_to_eid[spider_idx]
            hif_add_incidence(hif_hg, eid, nid, role="dom", index=idx, key=None)
            
        for idx, spider_idx in enumerate(outs):
            eid = spider_to_eid[spider_idx]
            hif_add_incidence(hif_hg, eid, nid, role="cod", index=idx, key=None)
            
    return hif_hg
