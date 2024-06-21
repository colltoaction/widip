import sys
import warnings

from discopy.frobenius import Category, Functor, Ty, Box
from discopy.frobenius import Hypergraph as H, Id, Spider

from widip.files import stream_diagram
from .shell import shell_f, add_io_f


warnings.filterwarnings("ignore")
match sys.argv:
    case [_, file_name]:
        diagram = stream_diagram(open(file_name))
        diagram = add_io_f(diagram)
        shell_result = shell_f(diagram)(None)
        print("".join(shell_result), end="")
