import pathlib
import sys

from bin.yaml import shell_main


file_names = sys.argv[1:]
if not file_names:
    file_names = [pathlib.Path("bin/yaml/shell.yaml")]
    while True:
        try:
            shell_main(file_names)
        except EOFError:
            exit(0)
else:
    shell_main(file_names)
