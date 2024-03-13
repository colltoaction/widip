import pathlib
from src import diagram_functor, box_fun_functor
from files import path_diagram

do_control = lambda ar: lambda *xs: \
        xs[0] if ar.name == "const" else \
        xs[0](xs[1]) if ar.name == "map" else \
        (lambda x: x, xs[0]) if ar.name == "pure" else \
        xs[0](xs[1]) if ar.name == "contramap" else ()
do_map_functor = box_fun_functor(do_control)
functor_diagram = path_diagram(pathlib.Path("src/control/functor.yaml"))
control_f = diagram_functor(functor_diagram) \
    >> do_map_functor
