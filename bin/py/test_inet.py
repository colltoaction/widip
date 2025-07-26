import networkx as nx
from .inet import *



def test_self_connect_secondary_ports():
    inet = nx.MultiGraph()
    c = inet_add_construct(inet)
    inet_connect_ports(inet, (c, 1), (c, 2))
    assert len(inet.nodes) == 5
    assert len(inet.edges) == 3
    # multiedge
    assert len(inet[4][0]) == 2


def test_connect_ports():
    inet = nx.MultiGraph()
    c = inet_add_construct(inet)
    d = inet_add_duplicate(inet)
    assert len(inet.nodes) == 8
    assert len(inet.edges) == 6
    inet_connect_ports(inet, (c, 0), (d, 0))
    e = inet_add_erase(inet)
    assert len(inet.edges) == 7
    inet_connect_ports(inet, (e, 0), (c, 1))
    assert len(inet.edges) == 7


def test_annihilate_erase_erase():
    inet = nx.MultiGraph()
    u = inet_add_erase(inet)
    v = inet_add_erase(inet)
    inet_connect_ports(inet, (u, 0), (v, 0))
    annihilate_erase_erase(inet)
    assert len(inet.edges) == 0


def test_commute_construct_duplicate():
    inet = nx.MultiGraph()
    u = inet_add_construct(inet)
    v = inet_add_duplicate(inet)
    inet_connect_ports(inet, (u, 0), (v, 0))
    commute_construct_duplicate(inet)
    assert len(inet.edges) == 12


def test_franchus_inet():
    inet = nx.MultiGraph()
    u = inet_add_construct(inet)
    v = inet_add_duplicate(inet)
    w = inet_add_construct(inet)
    inet_connect_ports(inet, (u, 0), (v, 0))
    inet_connect_ports(inet, (u, 1), (u, 2))
    inet_connect_ports(inet, (v, 1), (w, 1))
    inet_connect_ports(inet, (v, 2), (w, 0))
    commute_construct_duplicate(inet)
    # TODO this applies both but we might want
    # to do one reduction at a time
    annihilate_concon_or_dupdup(inet)
    assert len(inet.edges) == 3
    # self reference multiedge
    assert len(inet[16][37]) == 2