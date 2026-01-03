import sys
import argparse
import asyncio
import contextlib
from pathlib import Path

from .exec import ExecFunctor
from .interactive import interpreter, read_single, read_shell
from .watch import run_with_watcher
from .compiler import SHELL_COMPILER
from .files import repl_read, file_diagram

@contextlib.contextmanager
def setup_runner():
    sys.setrecursionlimit(10000)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    runner = ExecFunctor(executable=sys.executable, loop=loop)
    try:
        yield runner, loop
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

def parse_args():
    parser = argparse.ArgumentParser(description="Widip")
    parser.add_argument("-c", dest="command_string")
    parser.add_argument("operands", nargs=argparse.REMAINDER)
    return parser.parse_args()

def setup_source(command_string, operands, runner):
    if command_string is not None:
        return read_single(repl_read(command_string), None, runner, operands), False
    elif operands:
        file_name = operands[0]
        fd = file_diagram(file_name)
        return read_single(fd, Path(file_name), runner, operands[1:]), False
    else:
        return read_shell(runner, sys.executable), True

def main(command_string, operands):
    with setup_runner() as (runner, loop):
        source, is_shell = setup_source(command_string, operands, runner)
            
        coro = interpreter(runner, SHELL_COMPILER, source)
        if is_shell:
            coro = run_with_watcher(coro)
        loop.run_until_complete(coro)

if __name__ == "__main__":
    if __debug__:
        import matplotlib
        matplotlib.use('agg')
    
    args = parse_args()
    main(args.command_string, args.operands)
