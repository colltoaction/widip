import asyncio
import sys
from pathlib import Path
from watchfiles import awatch
from yaml import YAMLError

from discopy.utils import tuplify

from .loader import repl_read
from .files import diagram_draw, file_diagram
from .widish import SHELL_RUNNER
from .compiler import SHELL_COMPILER, force


# TODO watch functor ??

def reload_diagram(path_str):
    print(f"reloading {path_str}")
    try:
        fd = file_diagram(path_str)
        diagram_draw(Path(path_str), fd)
        diagram_draw(Path(path_str+".2"), fd)
    except YAMLError as e:
        print(e)

async def handle_changes():
    # watchfiles awatch yields sets of changes
    async for changes in awatch('.', recursive=True):
        for change_type, path_str in changes:
             if path_str.endswith(".yaml"):
                 reload_diagram(path_str)

async def async_shell_main(file_name):
    path = Path(file_name)
    loop = asyncio.get_running_loop()

    # Start watcher
    print(f"watching for changes in current path")
    watcher_task = asyncio.create_task(handle_changes())

    try:
        while True:
            try:
                prompt = f"--- !{file_name}\n"
                # Use run_in_executor for blocking input
                source = await loop.run_in_executor(None, input, prompt)
                
                source_d = repl_read(source)
                if __debug__:
                    diagram_draw(path, source_d)
                compiled_d = source_d
                # compiled_d = SHELL_COMPILER(source_d)
                # if __debug__:
                #     diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)
                constants = tuple(x.name for x in compiled_d.dom)
                result_ev = SHELL_RUNNER(compiled_d)(*constants)
                print(force(result_ev))
            except EOFError:
                print("⌁")
                break
            except KeyboardInterrupt:
                print()
            except YAMLError as e:
                print(e)
    finally:
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass

async def async_widish_main(file_name, *shell_program_args: str):
    loop = asyncio.get_running_loop()
    
    fd = file_diagram(file_name)
    path = Path(file_name)
    if __debug__:
        diagram_draw(path, fd)
    constants = tuple(x.name for x in fd.dom)
    fd = SHELL_COMPILER(fd)
    if __debug__:
        diagram_draw(path.with_suffix(".shell.yaml"), fd)
    runner = SHELL_RUNNER(fd)(*constants)

    if sys.stdin.isatty():
        inp = ""
    else:
        inp = await loop.run_in_executor(None, sys.stdin.read)
        
    run_res = runner(inp)
    val = force(run_res)
    print(*(tuple(x.rstrip() for x in tuplify(val) if x)), sep="\n")

def widish_main(file_name, *shell_program_args: str):
    # Deprecated sync wrapper
    asyncio.run(async_widish_main(file_name, *shell_program_args))

async def main():
    match sys.argv:
        case [_]:
            try:
                await async_shell_main("bin/yaml/shell.yaml")
            except KeyboardInterrupt:
                pass
        case [_, file_name, *args]: 
            await async_widish_main(file_name, *args)
