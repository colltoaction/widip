import asyncio
import sys
from pathlib import Path
from yaml import YAMLError

from discopy.utils import tuplify

from .files import reload_diagram
from .loader import repl_read
from .widish import SHELL_RUNNER
from .thunk import unwrap


async def handle_changes():
    from watchfiles import awatch
    async for changes in awatch('.', recursive=True):
        for change_type, path_str in changes:
            if path_str.endswith(".yaml"):
                reload_diagram(path_str)

async def async_shell_main(file_name):
    path = Path(file_name)
    loop = asyncio.get_running_loop()

    # Start watcher
    watcher_task = None
    if __debug__:
        if sys.stdin.isatty():
            print(f"watching for changes in current path", file=sys.stderr)
        watcher_task = asyncio.create_task(handle_changes())

    try:
        while True:
            try:
                if not sys.stdin.isatty():
                    source = await loop.run_in_executor(None, sys.stdin.read)
                    if not source:
                        break
                else:
                    prompt = f"--- !{file_name}\n"
                    source = await loop.run_in_executor(None, input, prompt)

                source_d = repl_read(source)
                if __debug__:
                    from .files import diagram_draw
                    diagram_draw(path, source_d)
                compiled_d = source_d
                # compiled_d = SHELL_COMPILER(source_d)
                # if __debug__:
                #     diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)
                constants = tuple(x.name for x in compiled_d.dom)
                result_ev = SHELL_RUNNER(compiled_d)(*constants)
                result = await unwrap(result_ev)
                print(*(tuple(x.rstrip() for x in tuplify(result) if x)), sep="\n")

                if not sys.stdin.isatty():
                    break
            except EOFError:
                if sys.stdin.isatty():
                    print("⌁", file=sys.stderr)
                break
            except KeyboardInterrupt:
                print(file=sys.stderr)
            except YAMLError as e:
                print(e, file=sys.stderr)
    finally:
        if watcher_task:
            watcher_task.cancel()
            try:
                await watcher_task
            except asyncio.CancelledError:
                pass
