import sys
import os
from io import BytesIO
from pathlib import Path
from typing import Any
from functools import partial

from yaml import YAMLError
from discopy.closed import Diagram
from nx_yaml import nx_compose_all

from .loader import incidences_to_diagram
from .drawing import diagram_draw
from .compiler import SHELL_COMPILER as compiler
from .io import (
    read_stdin, 
    set_recursion_limit, 
    value_to_bytes, 
    stdout_write,
    stdin_read, 
    stdin_isatty, 
    get_executable
)
from .asyncio import async_read, run_repl, run
from .exec import widip_runner


# --- File I/O (merged from files.py) ---

def read_diagram(source: Any) -> Diagram:
    """Parse a stream or file path into a diagram."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        with path.open() as f:
            return read_diagram(f)
    incidences = nx_compose_all(source)
    return incidences_to_diagram(incidences)


def reload_diagram(path_str):
    """Reload and redraw a diagram from a file."""
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = read_diagram(path_str)
        if hasattr(fd, "simplify"):
            fd = fd.simplify()
        diagram_draw(Path(path_str), fd)
    except YAMLError as e:
        print(e, file=sys.stderr)


# --- Input Reading (Read) ---

def read(fd: Any | None, path: Path | None, file_name: str, loop: Any, hooks: dict):
    """Get the async reader iterator."""
    return async_read(fd, path, file_name, loop, read_diagram, read_stdin, hooks)


# --- Runtime Setup (Environment) ---

def env_fn():
    import argparse
    parser = argparse.ArgumentParser(prog="widip")
    parser.add_argument("-c", dest="command_string", help="Execute command string")
    parser.add_argument("-w", "--watch", action="store_true", help="Watch file for changes")
    parser.add_argument("operands", nargs="*", help="File to execute and/or arguments")
    return parser.parse_args()


def get_source(command_string: str | None, operands: list[str], loop, hooks: dict):
    """Get the source diagram iterator based on command line args."""
    executable = hooks['get_executable']()
    if command_string is not None:
         return read(read_diagram(command_string), None, executable, loop, hooks)
    elif operands:
         file_name = operands[0]
         fd = read_diagram(file_name)
         return read(fd, Path(file_name), file_name, loop, hooks)
    else:
         return read(None, None, executable, loop, hooks)


# --- Eval and Print (separate concerns) ---

def make_pipeline(runner):
    """Create execution pipeline."""
    return lambda fd: runner(compiler(fd, compiler, None))


# --- Main Entry Points ---

async def async_repl():
    """Main Read-Eval-Print Loop entry point (async)."""
    hooks = {
        'set_recursion_limit': set_recursion_limit,
        'value_to_bytes': value_to_bytes,
        'stdout_write': stdout_write,
        'stdin_read': stdin_read,
        'stdin_isatty': stdin_isatty,
        'get_executable': get_executable,
        'fspath': os.fspath,
        'BytesIO': BytesIO,
        'Path': Path
    }
    
    await run_repl(env_fn, widip_runner, get_source, make_pipeline, reload_diagram, hooks)


def repl():
    try:
        run(async_repl())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    repl()