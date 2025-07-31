import networkx as nx
from .inet import *


def test_connect_ports():
    inet = nx.MultiDiGraph()
    c = inet_add_construct(inet)
    d = inet_add_duplicate(inet)
    assert len(inet.nodes) == 8
    assert len(inet.edges) == 6
    inet_connect_ports(inet, (c, 0), (d, 0))
    e = inet_add_erase(inet)
    assert len(inet.edges) == 7
    inet_connect_ports(inet, (e, 0), (c, 1))
    assert len(inet.edges) == 7


def test_self_connect_secondary_ports():
    inet = nx.MultiDiGraph()
    c = inet_add_construct(inet)
    inet_connect_ports(inet, (c, 1), (c, 2))
    assert len(inet.nodes) == 5
    assert len(inet.edges) == 3
    # multiedge
    assert len(inet[4][0]) == 2


def test_annihilate_erase_erase():
    inet = nx.MultiDiGraph()
    u = inet_add_erase(inet)
    v = inet_add_erase(inet)
    inet_connect_ports(inet, (u, 0), (v, 0))
    annihilate_erase_erase(inet)
    assert len(inet.edges) == 0


def test_commute_construct_duplicate():
    inet = nx.MultiDiGraph()
    u = inet_add_construct(inet)
    v = inet_add_duplicate(inet)
    inet_connect_ports(inet, (u, 0), (v, 0))
    commute_construct_duplicate(inet)
    assert len(inet.edges) == 12


def test_annihilate_construct_construct():
    inet = nx.MultiDiGraph()
    u = inet_add_construct(inet)
    v = inet_add_construct(inet)
    inet_connect_ports(inet, (u, 0), (v, 0))
    annihilate_concon_or_dupdup(inet)
    assert len(inet.edges) == 0


def test_annihilate_duplicate_duplicate():
    inet = nx.MultiDiGraph()
    u = inet_add_duplicate(inet)
    v = inet_add_duplicate(inet)
    inet_connect_ports(inet, (u, 0), (v, 0))
    annihilate_concon_or_dupdup(inet)
    assert len(inet.edges) == 0


def test_annihilate_duplicate_duplicate_2():
    inet = nx.MultiDiGraph()
    u = inet_add_duplicate(inet)
    v = inet_add_duplicate(inet)
    e = inet_add_erase(inet)
    inet_connect_ports(inet, (u, 0), (v, 0))
    inet_connect_ports(inet, (u, 1), (e, 0))
    annihilate_concon_or_dupdup(inet)
    assert len(inet.edges) == 1


def test_franchus_inet():
    inet = nx.MultiDiGraph()
    u = inet_add_construct(inet)
    v = inet_add_duplicate(inet)
    w = inet_add_construct(inet)
    e = inet_add_erase(inet)
    inet_connect_ports(inet, (u, 0), (v, 0))
    inet_connect_ports(inet, (u, 1), (u, 2))
    inet_connect_ports(inet, (v, 1), (w, 1))
    inet_connect_ports(inet, (v, 2), (w, 0))
    inet_connect_ports(inet, (e, 0), (w, 2))
    commute_construct_duplicate(inet)
    annihilate_concon_or_dupdup(inet)
    annihilate_concon_or_dupdup(inet)
    assert len(inet.edges) == 4
    # self reference multiedge
    assert len(inet[40][19]) == 2
    commute_condup_erase(inet)
    assert len(inet.edges) == 2
    annihilate_erase_erase(inet)
    assert len(inet.edges) == 0

def test_annihilate_erase_erase_dpo():
    inet = nx.MultiDiGraph()
    u = inet_add_erase(inet)
    v = inet_add_erase(inet)
    w = inet_connect_ports(inet, (u, 0), (v, 0))
    rule = inet_eraera_rewrite_rule(inet, w)
    inet_rewrite(inet, rule)
    assert len(inet.edges) == 0

def test_condup_erase_dpo():
    inet = nx.MultiDiGraph()
    u = inet_add_construct(inet)
    v = inet_add_erase(inet)
    w = inet_connect_ports(inet, (u, 0), (v, 0))
    rule = inet_condup_erase_rewrite_rule(inet, w)
    inet_rewrite(inet, rule)
    assert len(inet.edges) == 2

def test_concon_or_dupdup_dpo():
    inet = nx.MultiDiGraph()
    u = inet_add_construct(inet)
    v = inet_add_construct(inet)
    a = inet_add_duplicate(inet)
    b = inet_add_duplicate(inet)
    w = inet_connect_ports(inet, (u, 0), (v, 0))
    inet_connect_ports(inet, (u, 1), (a, 0))
    inet_connect_ports(inet, (v, 1), (b, 0))
    rule = inet_concon_or_dupdup_rewrite_rule(inet, w)
    inet_rewrite(inet, rule)
    assert len(inet.edges) == 6
    [], [], [], [(w2, _, _)] = find_active_wires(inet)
    rule = inet_concon_or_dupdup_rewrite_rule(inet, w2)
    inet_rewrite(inet, rule)
    assert len(inet.edges) == 0