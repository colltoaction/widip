import sys

# Stop starting a Matplotlib GUI
import matplotlib
matplotlib.use('agg')

from .watch import watch_main, shell_main, widish_main


match sys.argv:
    case [_]:
        watch_main()
        shell_main("bin/yaml/shell.yaml")
    case [_, file_name]: widish_main(file_name)
