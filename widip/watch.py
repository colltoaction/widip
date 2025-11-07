from pathlib import Path
import sys
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from yaml import YAMLError

from discopy.frobenius import Id, Hypergraph as H, Ty, Box, Spider

from .loader import repl_read
from .files import diagram_draw, file_diagram
from .widish import SHELL_RUNNER, compile_shell_program


# TODO watch functor ??

class ShellHandler(FileSystemEventHandler):
    """Reload the shell on change."""
    def on_modified(self, event):
        if ".yaml" in event.src_path:
            print(f"reloading {event.src_path}")
            try:
                fd = file_diagram(str(event.src_path))
                diagram_draw(event.src_path, fd)
            except YAMLError as e:
                print(e)

def watch_main():
    """the process manager for the reader and """
    #  TODO watch this path to reload changed files,
    # returning an IO as always and maintaining the contract.
    print(f"watching for changes in current path")
    observer = Observer()
    shell_handler = ShellHandler()
    observer.schedule(shell_handler, ".", recursive=True)
    observer.start()
    return observer

def shell_main(file_name):
    try:
        while True:
            observer = watch_main()
            try:
                prompt = f"--- !{file_name}\n"
                source = input(prompt)
                source_d = repl_read(source)
                source_d.draw(
                        textpad=(0.3, 0.1),
                        fontsize=12,
                        fontsize_types=8)
                result_ev = SHELL_RUNNER(source_d)()
                print(result_ev)
            except KeyboardInterrupt:
                print()
            except YAMLError as e:
                print(e)
            finally:
                observer.stop()
    except EOFError:
        print("⌁")
        exit(0)

def widish_main(file_name, *shell_program_args: str):
    fd = file_diagram(file_name)
    fd = compile_shell_program(fd)
    fd = Spider(0, 1, Ty("io")) \
        >> fd \
        >> Spider(len(fd.cod), 1, Ty("io"))
    path = Path(file_name)
    diagram_draw(path, fd)
    result_ev = SHELL_RUNNER(fd)()
    print(result_ev)
