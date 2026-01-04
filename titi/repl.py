import sys
import os
from typing import Any
from functools import partial


from discopy import closed

from computer.yaml import load as load_diagram
from computer.yaml.presentation import CharacterStream
from computer.drawing import diagram_draw
from computer.io import (
    read_diagram_file as read_diagram_file_diag,
    impl_read_diagram_file as read_diagram_file_fn,
    read_stdin as read_stdin_diag,
    impl_read_stdin as read_stdin_fn,
    impl_set_recursion_limit as set_recursion_limit,
    value_to_bytes as value_to_bytes_diag,
    impl_value_to_bytes as value_to_bytes_fn,
    impl_stdout_write as stdout_write,
    impl_stdin_read as stdin_read,
    impl_stdin_isatty as stdin_isatty,
    impl_get_executable as get_executable,
    BytesIO,
    Path
)
from computer.asyncio import async_read, run_repl, run, loop_scope, eval_diagram
from computer.exec import execute, titi_runner



# --- File I/O ---

def read_diagram(source: Any) -> closed.Diagram:
    """Parse a stream or file path into a diagram."""
    return read_diagram_file_fn(source, lambda x: load_diagram(CharacterStream(x)))


def reload_diagram(path_str):
    """Reload and redraw a diagram from a file."""
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = read_diagram(path_str)
        if hasattr(fd, "simplify"):
            fd = fd.simplify()
        diagram_draw(Path(path_str), fd)
    except ValueError as e:
        print(e, file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)


# --- Input Reading ---

def read(fd: Any | None, path: Path | None, file_name: str, loop: Any, hooks: dict):
    """Get the async reader iterator."""
    return async_read(fd, path, file_name, loop, read_diagram, read_stdin_fn, hooks)


# --- Runtime Setup ---

def env_fn():
    import argparse
    parser = argparse.ArgumentParser(prog="titi")
    parser.add_argument("-c", dest="command_string", help="Execute command string")
    parser.add_argument("-w", "--watch", action="store_true", help="Watch file for changes")
    parser.add_argument("operands", nargs="*", help="File to execute and/or arguments")
    return parser.parse_args()


class SourceArgs:
    """Helper to structure return from get_params_fn."""
    def __init__(self, fd, path, file_name):
        self.fd = fd
        self.path = path
        self.file_name = file_name
    def __iter__(self):
        return iter((self.fd, self.path, self.file_name))

def get_source(command_string: str | None, operands: list[str], hooks: dict):
    """Get the source diagram parameters based on command line args."""
    executable = hooks['get_executable']()
    if command_string is not None:
         return SourceArgs(read_diagram(command_string), None, executable)
    elif operands:
         file_name = operands[0]
         return SourceArgs(read_diagram(file_name), Path(file_name), file_name)
    else:
         return SourceArgs(None, None, executable)


# --- Eval and Print ---

def make_pipeline(runner_data):
    """Create execution pipeline."""
    runner, loop = runner_data
    return lambda diag, stdin=None: runner(diag, stdin)


# --- Main Entry Point ---

async def async_repl():
    """Main Read-Eval-Print Loop entry point (async)."""
    hooks = {
        'set_recursion_limit': set_recursion_limit,
        'value_to_bytes': value_to_bytes_fn,
        'stdout_write': stdout_write,
        'stdin_read': stdin_read,
        'stdin_isatty': stdin_isatty,
        'get_executable': get_executable,
        'read_stdin_fn': read_stdin_fn,
        'read_diagram_file_fn': read_diagram_file_fn,
        'fspath': os.fspath,
        'BytesIO': BytesIO,
        'Path': Path
    }

    await run_repl(env_fn, titi_runner, get_source, read, make_pipeline, reload_diagram, hooks)


def repl():
    try:
        run(async_repl())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    repl()
