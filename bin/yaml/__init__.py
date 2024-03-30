import pathlib
from discopy.frobenius import Diagram, Box, Ty, Id

from bin.py.files import files_f, glue_all_diagrams
from bin.py.shell import shell_f


def shell_main(file_names):
    """a shell pipeline from the passed files"""
    file_names = map(pathlib.Path, file_names)
    rep_d = glue_all_diagrams((
        files_f(Box(f"file://./{path}", Ty(), Ty()))
        for path in file_names))
    rep_d = shell_f(rep_d)
    return rep_d
