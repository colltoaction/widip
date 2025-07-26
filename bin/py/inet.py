"""
A crude implementation of interaction nets
using NetworkX's MultiGraph with bipartite node structure:
* a node for each combinator
* a node for each wire
* each combinator is connected to one wire per port
* each wire is connected to one or two combinators
* a loop in a combinator require a multiedge
* disconnected wires and combinators are garbage
"""
import networkx as nx


def find_active_wires(inet: nx.MultiGraph):
    """Find all wires where interaction rules can be applied"""
    construct_duplicate = []
    erase_erase = []
    concon_or_dupdup = []
    condup_erase = []
    for u, d in inet.nodes(data=True):
        # u is a wire
        if d["bipartite"] == 0:
            # u connects two combinators
            if len(inet[u]) == 2:
                c1, c2 = inet[u]
                # u connects two principal ports at index 0
                if c1 != c2 and \
                    0 in inet[u][c1] and \
                    0 in inet[u][c2]:
                    c1tag = inet.nodes[c1]["tag"]
                    c2tag = inet.nodes[c2]["tag"]
                    if (c1tag, c2tag) == ("erase", "erase"):
                        erase_erase.append([u, c1, 0])
                        erase_erase.append([u, c2, 0])
                    if (c1tag, c2tag) == ("construct", "duplicate"):
                        construct_duplicate.append((u, c1, c2))
                    if (c1tag, c2tag) == ("duplicate", "construct"):
                        construct_duplicate.append((u, c2, c1))
                    if (c1tag, c2tag) == ("duplicate", "duplicate"):
                        concon_or_dupdup.append((u, c1, c2))
                    if (c1tag, c2tag) == ("construct", "construct"):
                        concon_or_dupdup.append((u, c1, c2))
                    if (c1tag, c2tag) == ("construct", "erase"):
                        condup_erase.append((u, c1, c2))
                    if (c1tag, c2tag) == ("erase", "construct"):
                        condup_erase.append((u, c2, c1))
                    if (c1tag, c2tag) == ("duplicate", "erase"):
                        condup_erase.append((u, c1, c2))
                    if (c1tag, c2tag) == ("erase", "duplicate"):
                        condup_erase.append((u, c2, c1))
    return construct_duplicate, erase_erase, condup_erase, concon_or_dupdup

def annihilate_erase_erase(inet: nx.MultiGraph):
    _, active_wires, _, _ = find_active_wires(inet)
    inet.remove_edges_from(active_wires)

def commute_construct_duplicate(inet: nx.MultiGraph):
    active_wires, _, _, _ = find_active_wires(inet)
    for u, c, d in active_wires:
        c0 = inet_add_construct(inet)
        c1 = inet_add_construct(inet)
        d0 = inet_add_duplicate(inet)
        d1 = inet_add_duplicate(inet)
        # wire secondary ports
        inet_connect_ports(inet, (c0, 1), (d0, 2))
        inet_connect_ports(inet, (c0, 2), (d1, 2))
        inet_connect_ports(inet, (c1, 1), (d0, 1))
        inet_connect_ports(inet, (c1, 2), (d1, 1))
        # rewire 2x2 secondary ports to 4 principals
        inet_replace_wire_end(inet, (c, 1), (d0, 0))
        inet_replace_wire_end(inet, (c, 2), (d1, 0))
        inet_replace_wire_end(inet, (d, 1), (c0, 0))
        inet_replace_wire_end(inet, (d, 2), (c1, 0))
        # isolate old combinators
        inet.remove_edges_from(list(inet.edges(u, keys=True)))
        inet.remove_edges_from(list(inet.edges(c, keys=True)))
        inet.remove_edges_from(list(inet.edges(d, keys=True)))

def commute_condup_erase(inet: nx.MultiGraph):
    _, _, active_wires, _ = find_active_wires(inet)
    for u, c, e in active_wires:
        d0 = inet_add_erase(inet)
        d1 = inet_add_erase(inet)
        inet_replace_port(inet, (d0, 0), (c, 2))
        inet_replace_port(inet, (d1, 0), (c, 1))
        # isolate old combinators
        inet.remove_edges_from(list(inet.edges(c, keys=True)))
        inet.remove_edges_from(list(inet.edges(e, keys=True)))

def annihilate_concon_or_dupdup(inet: nx.MultiGraph):
    _, _, _, active_wires = find_active_wires(inet)
    for u, c, d in active_wires:
        wc1 = inet_find_wire(inet, c, 1)
        wc2 = inet_find_wire(inet, c, 2)
        wd1 = inet_find_wire(inet, d, 1)
        wd2 = inet_find_wire(inet, d, 2)
        # isolate old combinators
        inet.remove_edges_from(list(inet.edges(u, keys=True)))
        inet.remove_edges_from(list(inet.edges(c, keys=True)))
        inet.remove_edges_from(list(inet.edges(d, keys=True)))
        # isolate old combinators
        w1 = inet.number_of_nodes()
        w2 = w1 + 1
        inet.add_node(w1, bipartite=0)
        inet.add_node(w2, bipartite=0)
        inet.add_edges_from(list((w1, y, z) for _, y, z in inet.edges(wc1, keys=True)))
        inet.add_edges_from(list((w1, y, z) for _, y, z in inet.edges(wd1, keys=True)))
        inet.add_edges_from(list((w2, y, z) for _, y, z in inet.edges(wc2, keys=True)))
        inet.add_edges_from(list((w2, y, z) for _, y, z in inet.edges(wd2, keys=True)))
        # isolate old wires
        inet.remove_edges_from(list(inet.edges(wc1, keys=True)))
        inet.remove_edges_from(list(inet.edges(wc2, keys=True)))
        inet.remove_edges_from(list(inet.edges(wd1, keys=True)))
        inet.remove_edges_from(list(inet.edges(wd2, keys=True)))

def inet_add_erase(inet: nx.MultiGraph):
    n = inet.number_of_nodes()
    inet.add_node(n, bipartite=1, tag="erase")
    inet.add_node(n+1, bipartite=0)
    inet.add_edge(n, n+1, key=0)
    return n

def inet_add_construct(inet: nx.MultiGraph):
    n = inet.number_of_nodes()
    inet.add_node(n, bipartite=1, tag="construct")
    inet.add_node(n+1, bipartite=0)
    inet.add_node(n+2, bipartite=0)
    inet.add_node(n+3, bipartite=0)
    inet.add_edge(n, n+1, key=0)
    inet.add_edge(n, n+2, key=1)
    inet.add_edge(n, n+3, key=2)
    return n

def inet_add_duplicate(inet: nx.MultiGraph):
    n = inet.number_of_nodes()
    inet.add_node(n, bipartite=1, tag="duplicate")
    inet.add_node(n+1, bipartite=0)
    inet.add_node(n+2, bipartite=0)
    inet.add_node(n+3, bipartite=0)
    inet.add_edge(n, n+1, key=0)
    inet.add_edge(n, n+2, key=1)
    inet.add_edge(n, n+3, key=2)
    return n

def inet_find_wire(inet: nx.MultiGraph, u, i):
    for w0, w1, j in inet.edges(u, keys=True):
        if i == j:
            return w1 if u == w0 else w0
    assert False

def inet_connect_ports(inet: nx.MultiGraph, p0, p1):
    u0, i0 = p0
    u1, i1 = p1
    w0 = inet_find_wire(inet, u0, i0)
    w1 = inet_find_wire(inet, u1, i1)
    inet.remove_edge(u0, w0)
    inet.remove_edge(u1, w1)
    w = inet.number_of_nodes()
    inet.add_node(w, bipartite=0)
    inet.add_edge(w, u0, key=i0)
    inet.add_edge(w, u1, key=i1)
    return w

def inet_replace_wire_end(inet: nx.MultiGraph, p0, p1):
    u0, i0 = p0
    u1, i1 = p1
    w0 = inet_find_wire(inet, u0, i0)
    w1 = inet_find_wire(inet, u1, i1)
    inet.remove_edge(u0, w0, key=i0)
    inet.remove_edge(u1, w1, key=i1)
    inet.add_edge(u1, w0, key=i1)

def inet_replace_port(inet: nx.MultiGraph, p0, p1):
    u0, i0 = p0
    u1, i1 = p1
    w0 = inet_find_wire(inet, u0, i0)
    w1 = inet_find_wire(inet, u1, i1)
    inet.remove_edge(u0, w0, key=i0)
    inet.remove_edge(u1, w1, key=i1)
    inet.add_edge(u0, w1, key=i0)
