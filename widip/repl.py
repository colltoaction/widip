from __future__ import annotations
import asyncio
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncIterator

from yaml import YAMLError
from discopy.closed import Diagram
from nx_yaml import nx_compose_all

from .loader import incidences_to_diagram
from .drawing import diagram_draw
from .computer import interpreter, compiler
from .io import loop_scope, printer, run_with_watcher, read_stdin
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

async def read(fd: Any | None, path: Path | None, file_name: str, loop: asyncio.AbstractEventLoop) -> AsyncIterator[tuple[Any, Path | None, Any]]:
    """Yields parsed diagrams from a file, command string, or shell prompt."""
    if fd is not None:
         input_stream = read_stdin()
         yield fd, path, input_stream
         return

    async for source_str in prompt_loop(file_name, loop):
        yield repl_read(source_str), Path(file_name), BytesIO(b"")


async def prompt_loop(file_name: str, loop: asyncio.AbstractEventLoop) -> AsyncIterator[str]:
    """Interactive prompt loop for REPL mode."""
    while True:
        try:
            if not sys.stdin.isatty():
                 source_str = sys.stdin.read()
            else:
                 prompt = f"--- !{file_name}\n"
                 source_str = await loop.run_in_executor(None, input, prompt)
        except (EOFError, KeyboardInterrupt):
            break

        if not source_str: 
             if not sys.stdin.isatty(): break
             continue
        yield source_str
        if not sys.stdin.isatty(): break


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


async def eval_diagram(pipeline, source, loop):
    """Evaluate diagrams through the pipeline."""
    return await interpreter(pipeline, source, loop, printer)


async def eval_with_watch(pipeline, source, loop):
    """Evaluate with file watching enabled."""
    await run_with_watcher(
        interpreter(pipeline, source, loop, printer),
        reload_fn=reload_diagram
    )


# --- Main Entry Points ---

async def async_repl():
    """Main Read-Eval-Print Loop entry point (async)."""
    args = env()
    
    with widip_runner(executable=sys.executable) as (runner, loop):
        # Read
        source = get_source(args.command_string, args.operands, loop)
        pipeline = make_pipeline(runner)

        # Eval & Print
        if args.watch and args.operands:
            await eval_with_watch(pipeline, source, loop)
        else:
            await eval_diagram(pipeline, source, loop)


def repl():
    try:
        asyncio.run(async_repl())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    repl()