import sys
import warnings

from .watch import watch_main, shell_main
from .widish import widish_main


warnings.filterwarnings("ignore")
match sys.argv:
    case [_]:
        watch_main()
        shell_main("bin/yaml/shell.yaml")
    case [_, file_name]: widish_main(file_name)
