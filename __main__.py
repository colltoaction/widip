import sys
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from bin.py import py_lisp_f
from bin.yaml import shell_main


class Main(FileSystemEventHandler):
    """Run the interpreter on file change."""
    def __init__(self):
        self.reload()
        super().__init__()

    def on_modified(self, event):
        print(f"Detected change in {event.src_path}, reloading...")
        self.reload()

    def reload(self):
        file_names = sys.argv[1:]
        if not file_names:
            file_names = ["bin/yaml/shell.yaml"]
        self.diagram = shell_main(file_names)

    def do(self):
        py_lisp_f(self.diagram)()

file_names = sys.argv[1:]
event_handler = Main()
if not file_names:
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()
    while True:
        try:
            event_handler.do()
        except EOFError:
            exit(0)
        except KeyboardInterrupt:
            observer.stop()
else:
    event_handler.do()
