import sys
import warnings

from .watch import watch_main, shell_main, stream_main


warnings.filterwarnings("ignore")
match sys.argv:
    case [_]:
        watch_main()
        shell_main("bin/yaml/shell.yaml")
    case [_, file_name]: stream_main(open(file_name))
