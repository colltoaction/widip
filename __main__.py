import pathlib
import sys
from files import compose_diagrams, file_functor, path_diagrams


def argv_diagrams():
    paths = iter(sys.argv[1:])
    for path in paths:
        yield from path_diagrams(pathlib.Path(path))

diagram = compose_diagrams(argv_diagrams())
diagram = file_functor(diagram)(diagram)
diagram.draw()
