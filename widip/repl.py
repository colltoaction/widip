from __future__ import annotations
import asyncio
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncIterator
from contextlib import contextmanager

from .files import repl_read, file_diagram
from .computer import interpreter, compiler
from .io import loop_scope, printer
from .exec import widip_runner
from .watch import run_with_watcher

# --- Input Reading (Read) ---

async def read(fd: Any | None, path: Path | None, file_name: str, loop: asyncio.AbstractEventLoop) -> AsyncIterator[tuple[Any, Path | None, Any]]:
    """Yields parsed diagrams from a file, command string, or shell prompt. (Impure)"""
    if fd is not None:
         input_stream = sys.stdin.buffer if not sys.stdin.isatty() else BytesIO(b"")
         yield fd, path, input_stream
         return

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
        yield repl_read(source_str), Path(file_name), BytesIO(b"")
        if not sys.stdin.isatty(): break

# --- Runtime Setup (Environment) ---

def env():
    import argparse
    parser = argparse.ArgumentParser(prog="widip")
    parser.add_argument("-c", dest="command_string", help="Execute command string")
    parser.add_argument("-w", "--watch", action="store_true", help="Watch file for changes")
    parser.add_argument("operands", nargs="*", help="File to execute and/or arguments")
    return parser.parse_args()

def get_source(args, loop):
    if args.command_string is not None:
         return read(repl_read(args.command_string), None, sys.executable, loop)
    elif args.operands:
         file_name = args.operands[0]
         fd = file_diagram(file_name)
         return read(fd, Path(file_name), file_name, loop)
    else:
         return read(None, None, sys.executable, loop)

async def eval_print(args, runner, loop, source):
    if args.watch and args.operands:
            await run_with_watcher(Path(args.operands[0]), runner, loop, compiler)
    else:
            pipeline = lambda fd: runner(compiler(fd, compiler, None))
            await interpreter(pipeline, source, loop, printer)

async def async_repl():
    """Main Read-Eval-Print Loop entry point (async)."""
    args = env()
    
    with loop_scope() as loop, widip_runner(executable=sys.executable, loop=loop) as runner:
        # 1. Read
        source = get_source(args, loop)

        # 2. Eval & Print
        await eval_print(args, runner, loop, source)

def repl():
    try:
        asyncio.run(async_repl())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    repl()