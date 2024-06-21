import subprocess

from discopy.frobenius import Category, Functor, Ty, Box
from discopy.frobenius import Hypergraph as H, Id, Spider

from bin.py.rep import PyFunction


# check examples/shell
# CWD=examples/shell python -m widish examples/shell/shell.yaml
def add_closed_io(diagram):
    dom = Spider(len(diagram.dom), 1, Ty("io")) @ Id().tensor(*(Spider(0, 1, t) for t in diagram.dom))
    cod = Spider(1, len(diagram.cod), Ty("io"))
    return dom >> Box(diagram.name, Ty("io") @ diagram.dom, Ty("io")) >> cod

add_io_f = Functor(
    lambda x: Ty("io"),
    lambda b: add_closed_io(b),)

shell_f = Functor(
    lambda x: x,
    lambda b: lambda io, *p: subprocess.run([b.name, *p], input=io or None, text=True, capture_output=True).stdout,
    cod=Category(Ty, PyFunction))
