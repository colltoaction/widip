import pathlib
import sys

from discopy.frobenius import Diagram

from bin.py import py_lisp_f
from bin.py.lisp import lisp_f
from composing import glue_all_diagrams
from files import file_diagram


if not sys.argv[1:]:
    while True:
        try:
            path = pathlib.Path("bin/yaml/lisp.yaml")
            rep_d = file_diagram(path.open())
            Diagram.to_gif(rep_d, path=str(path.with_suffix('.gif')))
            res = lisp_f(rep_d)
            res.draw()
        except EOFError:
            exit(0)
else:
    file_diagrams = []
    for file_name in sys.argv[1:]:
        path = pathlib.Path(file_name)
        fd = file_diagram(path.open())
        Diagram.to_gif(fd, path=str(path.with_suffix('.gif')))
        file_diagrams.append(fd)
    # TODO gif
    rep_d = glue_all_diagrams(file_diagrams)
    py_rep_d = lisp_f(rep_d)
    py_rep_d.draw()
    py_lisp_f(py_rep_d)()
