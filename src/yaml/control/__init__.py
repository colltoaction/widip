import pathlib
from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from src import diagram_functor
from files import path_diagram

functor_diagram = path_diagram(pathlib.Path("src/yaml/control/functor.yaml"))
control_f = diagram_functor(functor_diagram)
