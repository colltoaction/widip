import sys
from bin.py.watch import Main, watch_main


if sys.argv[1:]:
    file_name = sys.argv[1]
    main = Main(file_name)
    main.rep()
else:
    watch_main()
