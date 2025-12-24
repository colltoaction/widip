from nx_hif.hif import hif_node_incidences, hif_edge_incidences
from .traverse import vertical_map, p_functor

def cursor_step(cursor, key):
    node = p_functor(cursor)
    index = cursor[0]

    incidences = tuple(hif_node_incidences(node, index, key=key))
    if not incidences:
        return None
    ((edge, _, _, _), ) = incidences
    start = tuple(hif_edge_incidences(node, edge, key="start"))
    if not start:
        return None
    ((_, neighbor, _, _), ) = start

    return vertical_map(cursor, lambda _: neighbor)

def cursor_iter(cursor):
    curr = cursor_step(cursor, "next")
    while curr:
        yield curr
        curr = cursor_step(curr, "forward")
