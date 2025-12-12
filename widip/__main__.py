import sys

# Stop starting a Matplotlib GUI
import matplotlib
matplotlib.use('agg')

from .watch import shell_main, widish_main, widish_draw


match sys.argv:
    case [_, "--draw", file_name]:
        widish_draw(file_name)
    case [_]:
        shell_main("bin/yaml/shell.yaml")
    case [_, file_name, *args]: widish_main(file_name, *args)
