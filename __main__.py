import pathlib
import sys

from bin.py import py_lisp_f
from bin.yaml import shell_main


file_names = sys.argv[1:]
if not file_names:
    file_names = [pathlib.Path("bin/yaml/shell.yaml")]
    while True:
        try:
            d = shell_main(file_names)
            py_lisp_f(d)()
        except EOFError:
            exit(0)
else:
    d = shell_main(file_names)
    py_lisp_f(d)()
