import sys

# Stop starting a Matplotlib GUI
import matplotlib
matplotlib.use('agg')

from .watch import shell_main, widish_main


match sys.argv:
    case [_]:
        shell_main("bin/yaml/shell.yaml")
    case [_, file_name, *args]: widish_main(file_name, *args)
