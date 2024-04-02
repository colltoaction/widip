from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from discopy.frobenius import Diagram, Box, Ty, Id, Spider

from composing import adapt_to_interface, close_ty_f, replace_id_f

from .rep import py_rep_f
from .files import file_diagram, files_f
from .shell import shell_f


# TODO watch functor


class Main(FileSystemEventHandler):
    """Reload the file or dir functor on change."""
    def __init__(self, file_name):
        self.file_name = file_name
        self.reload()
        super().__init__()

    def watch(self):
        self.observer = Observer()
        self.observer.schedule(self, ".", recursive=True)
        self.observer.start()

    def reload(self):
        self.diagram = files_f(Box(f"file://./{self.file_name}", Ty("io"), Ty("io")))

    def on_modified(self, event):
        """Updates the file functor associated with the event"""
        super().on_modified(event)
        print(f"{event}")
        if ".yaml" in event.src_path:
            self.reload()

    def rep(self):
        """a shell pipeline from the passed files"""
        rep_d = self.diagram
        rep_d.draw()
        rep_d = shell_f(rep_d)
        # rep_d = close_ty_f("io")(rep_d)
        # rep_d.draw()
        # rep_d = files_f(rep_d)
        # TODO close IO
        rep_d = Id().tensor(*(
            Spider(0, 1, x)
            for x in rep_d.dom
        )) >> rep_d
        rep_d.draw()
        return py_rep_f(rep_d)()

def watch_main():
    #  TODO watch this path to reload changed files,
    # returning an IO as always and maintaining the contract.
    file_name = "bin/yaml/shell.yaml"
    # main = Main(file_name)
    # print(f"watching for changes in current path")
    # main.watch()
    while True:
        try:
            prompt = f"--- !{file_name}\n"
            line = input(prompt)
            line_d = file_diagram(line)
            line_d = Id().tensor(*(
                Spider(0, 1, x)
                for x in line_d.dom
            )) >> line_d
            close_ty_f
            # line_d = replace_id_f("io")(line_d)
            line_d.draw()
            line_d = shell_f(line_d)
            py_rep = py_rep_f(line_d)()
            print(py_rep)
        except EOFError:
            print("⌁")
            break
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            exit(0)

    # main.observer.stop()
    # main.observer.join()
    exit(0)
