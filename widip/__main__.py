from __future__ import annotations
import sys
import asyncio
import contextlib
from pathlib import Path
from typing import AsyncIterator, Any

from .exec import setup_loop, widip_runner
from .io import read_single, read_shell
from .interactive import interpreter
from .watch import run_with_watcher
from .compiler import SHELL_COMPILER
from .files import repl_read, file_diagram

@contextlib.contextmanager
def read(command_string: str | None, operands: list[str], loop: asyncio.AbstractEventLoop):
    """The 'read' role in the REPL: provides a context for the diagram source."""
    # Note: 'read' role is typically impure in Lisp/REPL terms, handling IO.
    # Yields (source, is_shell)
    
    if command_string is not None:
        yield read_single(repl_read(command_string), None, operands, loop), False
    elif operands:
        file_name = operands[0]
        fd = file_diagram(file_name)
        yield read_single(fd, Path(file_name), operands[1:], loop), False
    else:
        yield read_shell(sys.executable, loop), True

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(prog="widip")
    parser.add_argument("-c", dest="command_string", help="Execute command string")
    parser.add_argument("-w", "--watch", action="store_true", help="Watch file for changes")
    parser.add_argument("operands", nargs="*", help="File to execute and/or arguments")
    return parser.parse_args()

async def async_main():
    args = parse_args()
    
    with setup_loop() as loop:
        with widip_runner(executable=sys.executable, loop=loop) as runner:
            with read(args.command_string, args.operands, loop) as (source, is_shell):
                if args.watch and not is_shell:
                    # Watch mode
                    file_path = Path(args.operands[0])
                    await run_with_watcher(file_path, runner, loop, SHELL_COMPILER)
                else:
                    # Standard or Shell mode
                    await interpreter(source, runner, loop)

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
