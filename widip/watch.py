import asyncio
import sys
from pathlib import Path

from discopy.utils import tuplify

from .loader import repl_read
from .files import file_diagram
from .widish import SHELL_RUNNER
from .thunk import unwrap
from .compiler import SHELL_COMPILER


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
