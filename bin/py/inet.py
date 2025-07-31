"""
A crude implementation of interaction nets
using NetworkX's MultiDiGraph with bipartite node structure:
* a node for each combinator
* a node for each wire
* each combinator is connected to one wire per port
* each wire is connected to one or two combinators
* a loop in a combinator require a multiedge
* disconnected wires and combinators are garbage

Directedness is added for rendering purposes:
* the key 0 is the principal wire and is always combinator->wire
* the keys 1 and 2 are the secondary wires and always wire->combinator
"""
import networkx as nx
from nx_hif import read_hif


# def find_open_principal_wires(inet: nx.MultiDiGraph):
#     for u in inet.nodes:
#         if is_open_wire(inet, u):

def find_active_wires(inet: nx.MultiDiGraph):
    """Find all wires where interaction rules can be applied"""
    construct_duplicate = []
    erase_erase = []
    concon_or_dupdup = []
    condup_erase = []
    for u in inet.nodes:
        if is_active_wire(inet, u):
            (c1, _), (c2, _) = inet.in_edges(u)
            c1tag = inet.nodes[c1]["tag"]
            c2tag = inet.nodes[c2]["tag"]
            if (c1tag, c2tag) == ("erase", "erase"):
                erase_erase.append([c1, u, 0])
                erase_erase.append([c2, u, 0])
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

def is_active_wire(inet: nx.MultiDiGraph, u):
    d = inet.nodes[u]
    if d["bipartite"] == 0:
        # u connects two combinators
        if inet.in_degree[u] == 2:
            return True
    return False

def find_open_wires(inet: nx.MultiDiGraph):
    principal_wires = []
    auxiliary_wires = []
    for u, d in inet.nodes(data=True):
        if d["bipartite"] == 0:
            # u has exactly one edge
            if inet.in_degree[u] + inet.out_degree[u] == 1:
                if inet.in_degree[u] == 1:
                    principal_wires.append(u)
                else:
                    auxiliary_wires.append(u)
    return principal_wires, auxiliary_wires

def inet_union(a: nx.MultiDiGraph, b: nx.MultiDiGraph):
    """
    A union cleans up garbage nodes, renames to avoid collisions
    """
    inet = nx.convert_node_labels_to_integers(b, a.number_of_nodes())
    inet.update(a.edges(data=True, keys=True), a.nodes(data=True))
    return inet

def annihilate_erase_erase(inet: nx.MultiDiGraph):
    _, active_wires, _, _ = find_active_wires(inet)
    inet.remove_edges_from(active_wires)

def commute_construct_duplicate(inet: nx.MultiDiGraph):
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

def commute_condup_erase(inet: nx.MultiDiGraph):
    _, _, active_wires, _ = find_active_wires(inet)
    for u, c, e in active_wires:
        d0 = inet_add_erase(inet)
        d1 = inet_add_erase(inet)
        inet_replace_port(inet, (d0, 0), (c, 2))
        inet_replace_port(inet, (d1, 0), (c, 1))
        # isolate old combinators
        inet.remove_edges_from(list(inet.edges(c, keys=True)))
        inet.remove_edges_from(list(inet.edges(e, keys=True)))

def annihilate_concon_or_dupdup(inet: nx.MultiDiGraph):
    _, _, _, active_wires = find_active_wires(inet)
    for u, c, d in active_wires:
        wc1 = inet_find_wire(inet, c, 1)
        wc2 = inet_find_wire(inet, c, 2)
        wd1 = inet_find_wire(inet, d, 1)
        wd2 = inet_find_wire(inet, d, 2)
        w1 = inet.number_of_nodes()
        w2 = w1 + 1
        # repeated wire
        if len({wc1, wc2, wd1, wd2}) < 4:
            w2 = w1
        inet.add_node(w1, bipartite=0)
        inet.add_node(w2, bipartite=0)
        inet.add_edges_from(list((y, w1, z, d) for y, _, z, d in inet.in_edges(wc1, keys=True, data=True)))
        inet.add_edges_from(list((w1, y, z, d) for _, y, z, d in inet.out_edges(wc1, keys=True, data=True)))
        inet.add_edges_from(list((y, w1, z, d) for y, _, z, d in inet.in_edges(wd1, keys=True, data=True)))
        inet.add_edges_from(list((w1, y, z, d) for _, y, z, d in inet.out_edges(wd1, keys=True, data=True)))
        inet.add_edges_from(list((y, w2, z, d) for y, _, z, d in inet.in_edges(wc2, keys=True, data=True)))
        inet.add_edges_from(list((w2, y, z, d) for _, y, z, d in inet.out_edges(wc2, keys=True, data=True)))
        inet.add_edges_from(list((y, w2, z, d) for y, _, z, d in inet.in_edges(wd2, keys=True, data=True)))
        inet.add_edges_from(list((w2, y, z, d) for _, y, z, d in inet.out_edges(wd2, keys=True, data=True)))
        # isolate old wires
        inet.remove_edges_from(list(inet.in_edges(wc1, keys=True)))
        inet.remove_edges_from(list(inet.out_edges(wc1, keys=True)))
        inet.remove_edges_from(list(inet.in_edges(wc2, keys=True)))
        inet.remove_edges_from(list(inet.out_edges(wc2, keys=True)))
        inet.remove_edges_from(list(inet.in_edges(wd1, keys=True)))
        inet.remove_edges_from(list(inet.out_edges(wd1, keys=True)))
        inet.remove_edges_from(list(inet.in_edges(wd2, keys=True)))
        inet.remove_edges_from(list(inet.out_edges(wd2, keys=True)))
        # isolate old combinators
        inet.remove_edges_from(list(inet.in_edges(c, keys=True)))
        inet.remove_edges_from(list(inet.out_edges(c, keys=True)))
        inet.remove_edges_from(list(inet.in_edges(d, keys=True)))
        inet.remove_edges_from(list(inet.out_edges(d, keys=True)))
        return

def inet_add_erase(inet: nx.MultiDiGraph):
    n = inet.number_of_nodes()
    inet.add_node(n, bipartite=1, tag="erase")
    inet.add_node(n+1, bipartite=0)
    inet.add_edge(n, n+1, key=0)
    return n

def inet_add_construct(inet: nx.MultiDiGraph):
    n = inet.number_of_nodes()
    inet.add_node(n, bipartite=1, tag="construct")
    inet.add_node(n+1, bipartite=0)
    inet.add_node(n+2, bipartite=0)
    inet.add_node(n+3, bipartite=0)
    inet.add_edge(n, n+1, key=0)
    inet.add_edge(n+2, n, key=1)
    inet.add_edge(n+3, n, key=2)
    return n

def inet_add_duplicate(inet: nx.MultiDiGraph):
    n = inet.number_of_nodes()
    inet.add_node(n, bipartite=1, tag="duplicate")
    inet.add_node(n+1, bipartite=0)
    inet.add_node(n+2, bipartite=0)
    inet.add_node(n+3, bipartite=0)
    inet.add_edge(n, n+1, key=0)
    inet.add_edge(n+2, n, key=1)
    inet.add_edge(n+3, n, key=2)
    return n

def inet_find_wire(inet: nx.MultiDiGraph, comb, port):
    assert inet.nodes[comb]["bipartite"] == 1
    if port == 0:
        for _, w1, _ in inet.out_edges(comb, keys=True):
            return w1
        assert False

    for w1, _, j in inet.in_edges(comb, keys=True):
        if port == j:
            return w1
    assert False

def inet_remove_wire_from_port(inet: nx.MultiDiGraph, comb, port):
    wire = inet_find_wire(inet, comb, port)
    if port == 0:
        inet.remove_edge(comb, wire, port)
    else:
        inet.remove_edge(wire, comb, port)
    return wire

def inet_add_wire_to_port(inet: nx.MultiDiGraph, comb, port, wire):
    if port == 0:
        inet.add_edge(comb, wire, port)
    else:
        inet.add_edge(wire, comb, port)

def inet_merge_many_wires(inet: nx.MultiDiGraph, ws):
    w = inet.number_of_nodes()
    inet.add_node(w, bipartite=0)
    for w0 in ws:
        inet.add_edges_from(list((y, w, z, d) for y, _, z, d in inet.in_edges(w0, data=True, keys=True)))
        inet.add_edges_from(list((w, y, z, d) for _, y, z, d in inet.out_edges(w0, data=True, keys=True)))
        inet.remove_edges_from(list(inet.in_edges(w0, keys=True)))
        inet.remove_edges_from(list(inet.out_edges(w0, keys=True)))
    return w

def inet_merge_wires(inet: nx.MultiDiGraph, w0, w1):
    return inet_merge_many_wires(inet, [w0, w1])

def inet_connect_ports(inet: nx.MultiDiGraph, p0, p1):
    u0, i0 = p0
    u1, i1 = p1
    w0 = inet_remove_wire_from_port(inet, u0, i0)
    w1 = inet_remove_wire_from_port(inet, u1, i1)
    w = inet.number_of_nodes()
    inet.add_node(w, bipartite=0)
    inet_add_wire_to_port(inet, u0, i0, w)
    inet_add_wire_to_port(inet, u1, i1, w)
    return w

def inet_replace_wire_end(inet: nx.MultiDiGraph, p0, p1):
    u0, i0 = p0
    u1, i1 = p1
    w0 = inet_remove_wire_from_port(inet, u0, i0)
    w1 = inet_remove_wire_from_port(inet, u1, i1)
    inet_add_wire_to_port(inet, u1, i1, w0)

def inet_replace_port(inet: nx.MultiDiGraph, p0, p1):
    u0, i0 = p0
    u1, i1 = p1
    w0 = inet_remove_wire_from_port(inet, u0, i0)
    w1 = inet_remove_wire_from_port(inet, u1, i1)
    inet_add_wire_to_port(inet, u0, i0, w1)


# TODO each active wire yields:
# * a subgraph match with both combinators
# * a replacement calculated based on the combinators interacting

#### DPO Rewriting
# https://en.wikipedia.org/wiki/Double_pushout_graph_rewriting
# this respects an interface
# 1. find a matching subgraph (e.g active wire + combinators)
# 2. identify subgraph nodes with replacement nodes
# 3. isolate subgraph nodes not in the replacement
# 4. plug in replacement
# def inet_rewrite(inet, left, right):

# for each rewrite we need to specify
# the two graphs but also which wires are mapped.
# giving a well-known ordering of the boundary wires
# e.g (wc1, wc2, wd1, wd2) in the case of con-dup,
# for both the match and replacement.
# this is the same as giving a graph
# between nodes in both graphs.

# TODO rules are static python code
# but they could be loaded at runtime.
def inet_find_active_subgraph(inet, w):
    combs = list(inet.predecessors(w))
    wires = [p for w in combs for p in inet.successors(w)]
    inet = inet.subgraph(combs + wires)
    return inet

def inet_eraera_rewrite_rule(inet, w):
    (c0, _), (c1, _) = inet.in_edges(w)
    match = inet.subgraph((w, c0, c1))
    replacement = nx.MultiDiGraph()
    boundary = nx.MultiDiGraph()
    return match, replacement, boundary

def inet_concon_or_dupdup_rewrite_rule(inet, w):
    (u, _), (v, _) = inet.in_edges(w)
    wu1 = inet_find_wire(inet, u, 1)
    wu2 = inet_find_wire(inet, u, 2)
    wv1 = inet_find_wire(inet, v, 1)
    wv2 = inet_find_wire(inet, v, 2)
    match = inet.subgraph([w, u, v, wu1, wu2, wv1, wv2])
    w = inet.number_of_nodes()
    replacement = nx.MultiDiGraph()
    replacement.add_nodes_from([wu1, wu2, wv1, wv2, w, w+1], bipartite=0)
    boundary = nx.MultiDiGraph()
    boundary.add_edge(wu1, w)
    boundary.add_edge(wu2, w+1)
    boundary.add_edge(wv1, w)
    boundary.add_edge(wv2, w+1)
    return match, replacement, boundary

def inet_condup_erase_rewrite_rule(inet, w):
    (u, _), (v, _) = inet.in_edges(w)
    c, e = (v, u) if inet.nodes[u]["tag"] == "erase" else (u, v)
    wc1 = inet_find_wire(inet, c, 1)
    wc2 = inet_find_wire(inet, c, 2)
    match = inet.subgraph([w, c, e, wc1, wc2])
    replacement = nx.MultiDiGraph()
    d0 = inet_add_erase(replacement)
    d1 = inet_add_erase(replacement)
    wd0 = inet_find_wire(replacement, d0, 0)
    wd1 = inet_find_wire(replacement, d1, 0)
    relabels = {r: r+match.number_of_nodes() if r in match else r for r in replacement}
    nx.relabel_nodes(replacement, relabels, copy=False)
    boundary = nx.MultiDiGraph()
    boundary.add_edge(wc2, relabels[wd0])
    boundary.add_edge(wc1, relabels[wd1])
    return match, replacement, boundary

def inet_rewrite(inet: nx.MultiDiGraph, rule):
    match, replacement, boundary = rule
    inet.add_edges_from(list(replacement.in_edges(data=True, keys=True)))
    inet.add_edges_from(list(replacement.out_edges(data=True, keys=True)))
    inet.add_nodes_from(list(replacement.nodes(data=True)))
    inet.remove_edges_from(list(match.in_edges(keys=True, data=True)))
    inet.remove_edges_from(list(match.out_edges(keys=True, data=True)))
    for w in boundary.nodes:
        if boundary.in_degree[w] > 0:
            inet_merge_many_wires(inet, [w]+list(boundary.predecessors(w)))
    return inet


#### IO using nx_hif

def inet_read_hif(path):
    # TODO add the ability to read references to other files
    inet = read_hif(path)
    inet = inet_clean(inet)
    return inet

def inet_clean(inet):
    inet.remove_nodes_from(list(nx.isolates(inet)))
    # TODO in-place
    inet = nx.convert_node_labels_to_integers(inet, 0)
    return inet


#### Lambda calculus as seen in
# https://zicklag.katharos.group/blog/interaction-nets-combinators-calculus/

def inet_lambda_id(inet: nx.MultiDiGraph):
    c = inet_add_construct(inet)
    inet_connect_ports(inet, (c, 1), (c, 2))
    return c

def inet_lambda(inet: nx.MultiDiGraph, arg, body):
    c = inet_add_construct(inet)
    inet_connect_ports(inet, (c, 1), arg)
    inet_connect_ports(inet, (c, 2), body)
    return c

def inet_apply(inet: nx.MultiDiGraph, arg, f):
    c = inet_add_construct(inet)
    inet_connect_ports(inet, (c, 1), arg)
    inet_connect_ports(inet, (c, 0), f)
    return c

#### Lambda calculus extended with nats as seen in
# https://stevenhuyn.bearblog.dev/succ/

def inet_zero(inet: nx.MultiDiGraph):
    i = inet_lambda_id(inet)
    c = inet_add_construct(inet)
    inet_connect_ports(inet, (c, 2), (i, 0))
    return c

def inet_succ(inet: nx.MultiDiGraph):
    ln = inet_add_construct(inet)
    lf = inet_add_construct(inet)
    lx = inet_add_construct(inet)
    a0 = inet_add_construct(inet)
    a1 = inet_add_construct(inet)
    a2 = inet_add_construct(inet)
    d = inet_add_duplicate(inet)
    inet_connect_ports(inet, (ln, 1), (a0, 0))
    inet_connect_ports(inet, (ln, 2), (lf, 0))
    inet_connect_ports(inet, (lf, 1), (d, 0))
    inet_connect_ports(inet, (lf, 2), (lx, 0))
    inet_connect_ports(inet, (a0, 1), (d, 1))
    inet_connect_ports(inet, (a0, 2), (a1, 0))
    inet_connect_ports(inet, (d, 2), (a2, 0))
    inet_connect_ports(inet, (lx, 1), (a1, 1))
    inet_connect_ports(inet, (lx, 2), (a2, 2))
    inet_connect_ports(inet, (a1, 2), (a2, 1))
    return ln

#### Drawing is still crude
# https://networkx.org/documentation/stable/auto_examples/drawing/plot_multigraphs.html

def inet_draw(inet):
    inet = nx.MultiDiGraph(inet)
    inet.remove_nodes_from(list(nx.isolates(inet)))
    # https://docs.rapids.ai/api/cugraph/stable/api_docs/api/cugraph/cugraph.force_atlas2/
    # note that this layout can be run on the GPU with nx-cugraph
    pos = nx.drawing.layout.forceatlas2_layout(inet)
    nx.draw_networkx(
        inet,
        pos=pos,
        labels={
            n: ("" if inet.nodes[n]["bipartite"] == 0
                else inet.nodes[n].get("tag")) for n in inet.nodes},
        node_size=[
            100 if is_active_wire(inet, n) else
            10 if inet.nodes[n]["bipartite"] == 0
            else 300 for n in inet.nodes],
        node_color=[
            "red" if is_active_wire(inet, n) else
            "blue" if inet.nodes[n]["bipartite"] == 0
            else "green" for n in inet.nodes],
        connectionstyle=["arc3,rad=-0.00", "arc3,rad=0.3"],
        )
