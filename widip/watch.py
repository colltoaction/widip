from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from yaml import YAMLError

from discopy.frobenius import Id, Hypergraph as H, Ty, Box

from .loader import repl_print, repl_read
from .files import file_diagram
from .widish import SHELL_RUNNER, compile_shell_program


# TODO watch functor ??

class ShellHandler(FileSystemEventHandler):
    """Reload the shell on change."""
    def __init__(self):
        super().__init__()

    def on_modified(self, event):
        super().on_modified(event)
        if ".yaml" in event.src_path:
            print(f"reloading {event.src_path}")
            file_diagram(str(event.src_path))

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
    try:
        repl_env = compile_shell_program
        while True:
            try:
                prompt = f"--- !{file_name}\n"
                source = input(prompt)
                source_d = repl_read(source)
                result_d = repl_eval(source_d, repl_env)
                result_str = repl_print(result_d)
                print(result_str)
            except KeyboardInterrupt:
                print()
            except YAMLError as e:
                print(e)
    except EOFError:
        print("⌁")
        exit(0)

def widish_main(file_name, *shell_program_args):
    path = Path(file_name)
    source = path.open()
    program_d = repl_read(source)
    shell_program_d = compile_shell_program(program_d)
    shell_program_d.draw(path=path.with_suffix(".jpg"))
    result_ev = SHELL_RUNNER(shell_program_d)(*shell_program_args)
    print(result_ev)

def repl_eval(source_d, repl_env):
    shell_program_d = repl_env(source_d)
    shell_program_d.draw()
    shell_program_d = shell_program_d >> H.spiders(len(shell_program_d.cod), 1, Ty("io")).to_diagram()
    shell_stdout = SHELL_RUNNER(shell_program_d)("")
    print(shell_stdout)
    return Box(shell_stdout, Ty(), Ty())
