import asyncio
import sys
from pathlib import Path
from yaml import YAMLError

from discopy.utils import tuplify

from .loader import repl_read
from .files import file_diagram
from .widish import SHELL_RUNNER
from .thunk import unwrap
from .compiler import SHELL_COMPILER


# TODO watch functor ??

def reload_diagram(path_str):
    from .files import diagram_draw
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = file_diagram(path_str)
        diagram_draw(Path(path_str), fd)
        diagram_draw(Path(path_str+".2"), fd)
    except YAMLError as e:
        print(e, file=sys.stderr)

async def handle_changes():
    from watchfiles import awatch
    # watchfiles awatch yields sets of changes
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

async def async_exec_diagram(fd, path, *shell_program_args):
    loop = asyncio.get_running_loop()

    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path, fd)

    constants = tuple(x.name for x in fd.dom)
    compiled_d = SHELL_COMPILER(fd)

    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)
    runner = SHELL_RUNNER(compiled_d)(*constants)

    if sys.stdin.isatty():
        inp = ""
    else:
        inp = await loop.run_in_executor(None, sys.stdin.read)
        
    run_res = runner(inp)
    val = await unwrap(run_res)
    print(*(tuple(x.rstrip() for x in tuplify(val) if x)), sep="\n")


async def async_command_main(command_string, *shell_program_args):
    fd = repl_read(command_string)
    # No file path associated with command string
    await async_exec_diagram(fd, None, *shell_program_args)


async def async_widish_main(file_name, *shell_program_args):
    fd = file_diagram(file_name)
    path = Path(file_name)
    await async_exec_diagram(fd, path, *shell_program_args)
