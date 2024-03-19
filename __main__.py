import sys
from bin.lisp import rep
from files import file_diagram

if not sys.argv[1:]:
    while True:
        try:
            rep()
        except EOFError:
            exit(0)
else:
    print("TODO argv")
    exit(1)
