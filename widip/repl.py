import asyncio
import sys
import os
from io import BytesIO
from pathlib import Path
from typing import Any

from yaml import YAMLError
from discopy.closed import Diagram
from nx_yaml import nx_compose_all

from .loader import incidences_to_diagram
from .drawing import diagram_draw
from .computer import compiler
from .io import (
    read_stdin, 
    set_recursion_limit, 
    value_to_bytes, 
    stdout_write,
    stdin_read, 
    stdin_isatty, 
    get_executable
)
from .asyncio import async_read, run_repl, setup_hooks
from .exec import widip_runner


# --- File I/O (merged from files.py) ---

def repl_read(stream):
    """Parse a stream into a diagram."""
    incidences = nx_compose_all(stream)
    return incidences_to_diagram(incidences)


def file_diagram(file_name) -> Diagram:
    """Load a diagram from a file."""
    path = Path(file_name)
    return repl_read(path.open())


def reload_diagram(path_str):
    """Reload and redraw a diagram from a file."""
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = file_diagram(path_str)
        if hasattr(fd, "simplify"):
            fd = fd.simplify()
        diagram_draw(Path(path_str), fd)
    except YAMLError as e:
        print(e, file=sys.stderr)


# --- Input Reading (Read) ---

def read(fd: Any | None, path: Path | None, file_name: str, loop: Any):
    """Get the async reader iterator."""
    return async_read(fd, path, file_name, loop, repl_read, read_stdin)


# --- Runtime Setup (Environment) ---

def env():
    import argparse
    parser = argparse.ArgumentParser(prog="widip")
    parser.add_argument("-c", dest="command_string", help="Execute command string")
    parser.add_argument("-w", "--watch", action="store_true", help="Watch file for changes")
    parser.add_argument("operands", nargs="*", help="File to execute and/or arguments")
    return parser.parse_args()


def get_source(command_string: str | None, operands: list[str], loop):
    """Get the source diagram iterator based on command line args."""
    if command_string is not None:
         return read(repl_read(command_string), None, sys.executable, loop)
    elif operands:
         file_name = operands[0]
         fd = file_diagram(file_name)
         return read(fd, Path(file_name), file_name, loop)
    else:
         return read(None, None, sys.executable, loop)


# --- Eval and Print (separate concerns) ---

def make_pipeline(runner):
    """Create execution pipeline."""
    return lambda fd: runner(compiler(fd, compiler, None))


# --- Main Entry Points ---

async def async_repl():
    """Main Read-Eval-Print Loop entry point (async)."""
    setup_hooks(
        set_recursion_limit=set_recursion_limit,
        value_to_bytes=value_to_bytes,
        stdout_write=stdout_write,
        stdin_read=stdin_read,
        stdin_isatty=stdin_isatty,
        get_executable=get_executable,
        fspath=os.fspath,
        BytesIO=BytesIO,
        Path=Path
    )
    
    await run_repl(env, get_source, make_pipeline, widip_runner, reload_diagram)


def repl():
    try:
        asyncio.run(async_repl())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    repl()