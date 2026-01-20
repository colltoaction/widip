from pathlib import Path
import sys
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from yaml import YAMLError
from discopy.utils import tuplify, untuplify
from .loader import repl_read
from .files import diagram_draw, file_diagram
from .widish import SHELL_RUNNER

class ShellHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".yaml"):
            print(f"reloading {event.src_path}")
            try:
                fd = file_diagram(str(event.src_path))
                diagram_draw(Path(event.src_path), fd)
            except YAMLError as e:
                print(e)

def shell_main(file_name):
    try:
        while True:
            print("watching for changes in current path")
            observer = Observer()
            observer.schedule(ShellHandler(), ".", recursive=True)
            observer.start()
            try:
                source = input(f"--- !{file_name}\n")
                source_d = repl_read(source)
                diagram_draw(Path(file_name), source_d)
                constants = tuple(x.name for x in source_d.dom)
                print(SHELL_RUNNER(source_d)(*constants)(""))
            except KeyboardInterrupt:
                print()
            except YAMLError as e:
                print(e)
            finally:
                observer.stop()
    except EOFError:
        print("⌁")

def widish_main(file_name, *args):
    fd = file_diagram(file_name)
    diagram_draw(Path(file_name), fd)
    constants = tuple(x.name for x in fd.dom)
    runner = SHELL_RUNNER(fd)(*constants)
    result = runner("") if sys.stdin.isatty() else runner(sys.stdin.read())
    print(*(x.rstrip() for x in tuplify(untuplify(result)) if x), sep="\n")
