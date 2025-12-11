import unittest
from discopy.markov import Ty, Box, Hypergraph
from nx_hif.hif import hif_nodes, hif_edges, hif_edge_incidences

from .represent import to_hif

class TestRepresent(unittest.TestCase):
    def test_simple_box(self):
        x, y = Ty('x'), Ty('y')
        f = Box('f', x, y)

        # Use from_box as permitted now
        h = Hypergraph.from_box(f)

        nx_h = to_hif(h)

        # Check nodes (spiders)
        nodes = list(hif_nodes(nx_h))
        self.assertIn(0, nodes)
        self.assertIn(1, nodes)

        # Check edges
        edges = list(hif_edges(nx_h))
        self.assertIn("dom", edges)
        self.assertIn("cod", edges)
        box_edge = [e for e in edges if str(e).startswith("box_0_f")][0]

        # Check incidences
        # dom -> 0 (cod role)
        dom_incs = list(hif_edge_incidences(nx_h, "dom"))
        self.assertEqual(len(dom_incs), 1)
        # Structure is (edge, node, key, attrs)
        self.assertEqual(dom_incs[0][1], 0)

        # box f -> 0 (dom role), 1 (cod role)
        box_incs = list(hif_edge_incidences(nx_h, box_edge))
        self.assertEqual(len(box_incs), 2)

        # cod -> 1 (dom role)
        cod_incs = list(hif_edge_incidences(nx_h, "cod"))
        self.assertEqual(len(cod_incs), 1)
        self.assertEqual(cod_incs[0][1], 1)

    def test_composition(self):
        # x -> f -> y -> g -> z
        x, y, z = Ty('x'), Ty('y'), Ty('z')
        f = Box('f', x, y)
        g = Box('g', y, z)

        # Use from_box and composition
        h = Hypergraph.from_box(f) >> Hypergraph.from_box(g)

        nx_h = to_hif(h)

        nodes = list(hif_nodes(nx_h))
        # Spiders 0, 1, 2
        self.assertIn(0, nodes)
        self.assertIn(1, nodes)
        self.assertIn(2, nodes)

        edges = list(hif_edges(nx_h))
        self.assertIn("dom", edges)
        self.assertIn("cod", edges)

        f_edge = [e for e in edges if "box_0_f" in str(e)][0]
        g_edge = [e for e in edges if "box_1_g" in str(e)][0]

        # Check shared spider 1
        f_incs = list(hif_edge_incidences(nx_h, f_edge))
        g_incs = list(hif_edge_incidences(nx_h, g_edge))

        # Filter by role in attrs (index 3)
        f_cod = [inc for inc in f_incs if inc[3]["role"] == "cod"][0]
        g_dom = [inc for inc in g_incs if inc[3]["role"] == "dom"][0]

        self.assertEqual(f_cod[1], 1)
        self.assertEqual(g_dom[1], 1)

if __name__ == '__main__':
    unittest.main()
