from discopy.frobenius import Diagram, Box, Ty, Id

from bin.py.files import files_ar
from bin.py.shell import shell_f


def shell_main(file_names):
    """Read all files then run shells in parallel"""
    rep_d = Id().tensor(*(
        files_ar(Box('read', Ty(file_name), Ty()))
        for file_name in file_names))
    rep_d = shell_f(rep_d)
    return rep_d
