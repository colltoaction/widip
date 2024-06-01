from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from discopy.frobenius import Diagram, Box, Ty, Id, Spider

from bin.py.rep import py_rep_f
from bin.py.shell import shell_f

from .files import stream_diagram, files_f


# TODO watch functor

class ShellHandler(FileSystemEventHandler):
    """Reload the shell on change."""
    def __init__(self):
        super().__init__()

    def on_modified(self, event):
        super().on_modified(event)
        if ".yaml" in event.src_path:
            print(f"reloading {event.src_path}")
            files_f(Box(f"file://./{event.src_path}", Ty("io"), Ty("io")))

def watch_main():
    """the process manager for the reader and """
    #  TODO watch this path to reload changed files,
    # returning an IO as always and maintaining the contract.
    print(f"watching for changes in current path")
    observer = Observer()
    shell_handler = ShellHandler()
    observer.schedule(shell_handler, ".", recursive=True)
    observer.start()

def shell_main(file_name):
    while True:
        try:
            prompt = f"--- !{file_name}\n"
            py_rep = stream_main(input(prompt))
            print(py_rep)
        except EOFError:
            print("⌁")
            exit(0)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            exit(0)

def rep(prompt):
    # TODO wrap input in a closeable stream we control
    # it could use a timer with readline
    py_rep = stream_main(input(prompt))
    print(py_rep)

def stream_main(stream):
    stream_d = stream_to_diagram(stream)
    stream_d = shell_f(stream_d)
    return py_rep_f(stream_d)()

def stream_to_diagram(line):
    stream_d = stream_diagram(line)
    stream_d = Id().tensor(*(
                Spider(0, 1, x)
                for x in stream_d.dom
            )) >> stream_d
    # close_ty_f
    # line_d = replace_id_f("io")(line_d)
    # stream_d.draw()
    return stream_d
